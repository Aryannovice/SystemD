#include <mysql.h>
#include <iostream>
#include <queue>
#include <mutex>
#include <condition_variable>
#include <stdexcept>
#include <vector>
#include <thread>
#include <chrono>
#include <atomic>

// Thread-safe bounded blocking queue
template <typename T>
class BoundedBlockingQueue {
public:
    explicit BoundedBlockingQueue(size_t capacity) : capacity_(capacity) {}

    void push(T item) {
        std::unique_lock<std::mutex> lock(mtx_);
        cond_not_full_.wait(lock, [this] { return queue_.size() < capacity_; });
        queue_.push(std::move(item));
        cond_not_empty_.notify_one();
    }

    T pop() {
        std::unique_lock<std::mutex> lock(mtx_);
        cond_not_empty_.wait(lock, [this] { return !queue_.empty(); });
        T item = std::move(queue_.front());
        queue_.pop();
        cond_not_full_.notify_one();
        return item;
    }

    bool try_pop(T& item, int timeout_ms) {
        std::unique_lock<std::mutex> lock(mtx_);
        if (!cond_not_empty_.wait_for(lock, std::chrono::milliseconds(timeout_ms),
                                      [this] { return !queue_.empty(); })) {
            return false;
        }
        item = std::move(queue_.front());
        queue_.pop();
        cond_not_full_.notify_one();
        return true;
    }

private:
    std::queue<T> queue_;
    size_t capacity_;
    std::mutex mtx_;
    std::condition_variable cond_not_empty_;
    std::condition_variable cond_not_full_;
};

// Connection Pool
class ConnectionPool {
public:
    ConnectionPool(const char* host,
                   const char* user,
                   const char* password,
                   const char* db,
                   unsigned int port,
                   size_t poolSize)
        : queue_(poolSize), shutdown_(false) {
        for (size_t i = 0; i < poolSize; ++i) {
            MYSQL* conn = mysql_init(nullptr);
            if (!conn) throw std::runtime_error("mysql_init failed");

            if (!mysql_real_connect(conn, host, user, password, db, port, nullptr, 0)) {
                std::string err = mysql_error(conn);
                mysql_close(conn);
                throw std::runtime_error("Connection failed: " + err);
            }
            queue_.push(conn);
        }
    }

    MYSQL* acquire(int timeout_ms = 1000) {
    MYSQL* conn = nullptr;
    if (!queue_.try_pop(conn, timeout_ms)) {
        throw std::runtime_error("Timeout acquiring connection");
    }
    if (mysql_ping(conn) != 0) {
        // Return to pool before failing
        release(conn);
        throw std::runtime_error("Lost connection to MySQL");
    }
    return conn;
}

    void release(MYSQL* conn) {
        if (conn && !shutdown_) {
            queue_.push(conn);
        }
    }

    void shutdown() {
        shutdown_ = true;
        while (true) {
            MYSQL* conn = nullptr;
            if (!queue_.try_pop(conn, 10)) break;
            mysql_close(conn);
        }
    }

    ~ConnectionPool() {
        shutdown();
    }

private:
    BoundedBlockingQueue<MYSQL*> queue_;
    bool shutdown_;
};

// Example usage
int main() {
    try {
        ConnectionPool pool("127.0.0.1", "pooluser", "poolpass", "testdb", 3306, 3);

        auto runBatch = [&](int batchId, int requests, int timeout_ms) {
            std::atomic<int> ok{0}, fail{0};
            std::vector<std::thread> threads;
            threads.reserve(requests);

            for (int i = 0; i < requests; ++i) {
                threads.emplace_back([&, i] {
    MYSQL* conn = nullptr;
    bool acquired = false;

    try {
        conn = pool.acquire(timeout_ms);
        acquired = true;

        if (mysql_query(conn, "SELECT NOW()") == 0) {
    // Drain result set for SELECT
    MYSQL_RES* res = mysql_store_result(conn);
    if (res) {
        mysql_free_result(res);
        ok++;
    } else {
        // If SELECT expected a result but store_result failed
        if (mysql_field_count(conn) != 0) {
            fail++;
        } else {
            ok++;
        }
    }
} else {
    fail++;
}

        std::this_thread::sleep_for(std::chrono::milliseconds(200));
    } catch (...) {
        fail++;
    }

    if (acquired) {
        pool.release(conn);
    }
});
            }

            for (auto& t : threads) t.join();

            std::cout << "Batch " << batchId
                      << " finished. ok=" << ok.load()
                      << " fail=" << fail.load()
                      << " timeout_ms=" << timeout_ms
                      << "\n";
        };

        runBatch(1, 500, 1);
        runBatch(2, 500, 15000);

        pool.shutdown();
    } catch (const std::exception& e) {
        std::cerr << "Pool init failed: " << e.what() << "\n";
    }

    return 0;
}