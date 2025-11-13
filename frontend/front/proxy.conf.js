const PROXY_CONFIG = [
    {
        context: [
            '/debug/'
        ],
        target: 'http://localhost:8000/',
        changeOrigin: true,
        secure: false,
        logLevel: 'info'
    }
];

module.exports = PROXY_CONFIG;
