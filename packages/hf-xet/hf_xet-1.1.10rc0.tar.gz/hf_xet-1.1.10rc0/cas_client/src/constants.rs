utils::configurable_constants! {

    /// Retry at most this many times before permanently failing.
    ref CLIENT_RETRY_MAX_ATTEMPTS : usize = 5;

    /// On errors that can be retried, delay for this amount of time
    /// before retrying.
    ref CLIENT_RETRY_BASE_DELAY_MS : u64 = 3000;

    /// After this much time has passed since the first attempt,
    /// no more retries are attempted.
    ref CLIENT_RETRY_MAX_DURATION_MS: u64 = 6 * 60 * 1000; // 6m

    /// Cleanup idle connections that are unused for this amount of time.
    ref CLIENT_IDLE_CONNECTION_TIMEOUT_SECS: u64 = 60; // 1m

    /// Only no more than this number of idle connections in the connection pool.
    ref CLIENT_MAX_IDLE_CONNECTIONS: usize = 16;
}
