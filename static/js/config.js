// Конфигурация цветов для платформ
const PLATFORM_COLORS = {
    linkedin: '#0077B5',
    youtube: '#FF0000',
    medium: '#00AB6C',
    instagram: '#E4405F'
};

// Конфигурация для графиков
const CHART_CONFIG = {
    animation: {
        duration: 2000,
        easing: 'easeInOutQuart'
    },
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            position: 'top',
            labels: {
                font: {
                    size: 12
                },
                padding: 15,
                boxWidth: 15,
                boxHeight: 15
            }
        },
        title: {
            display: true,
            font: {
                size: 18
            },
            padding: {
                bottom: 20
            }
        }
    }
};

// Конфигурация для счетчиков
const COUNTER_CONFIG = {
    duration: 2000,
    interval: 20,
    digits: 5
};

// Экспортируем конфигурацию
export { PLATFORM_COLORS, CHART_CONFIG, COUNTER_CONFIG }; 