// Форматирование чисел
export function formatNumber(number) {
    return number.toLocaleString('ru-RU');
}

// Форматирование даты
export function formatDate(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString('ru-RU', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Вычисление процентов
export function calculatePercentage(value, total) {
    return ((value / total) * 100).toFixed(1);
}

// Анимация счетчика
export function animateCounter(element, targetValue, config) {
    const digits = element.querySelectorAll('.digit');
    let currentCount = 0;
    const totalDigits = config.digits;
    const stepValue = (targetValue - currentCount) / (config.duration / config.interval);

    const interval = setInterval(() => {
        currentCount += stepValue;
        const valueString = Math.round(currentCount).toString().padStart(totalDigits, '0');

        valueString.split('').forEach((digit, index) => {
            const digitElement = digits[index];
            digitElement.textContent = digit;
        });

        if (Math.abs(currentCount - targetValue) < 0.5) {
            clearInterval(interval);
        }
    }, config.interval);
}

// Обработка ошибок
export function handleError(error, element) {
    console.error('Error:', error);
    if (element) {
        element.textContent = 'Ошибка загрузки данных';
        element.classList.add('error');
    }
}

// Создание элемента с данными
export function createDataElement(platform, count, percentage) {
    const div = document.createElement('div');
    div.className = `percentage ${platform}`;
    div.innerHTML = `
        <span class="platform-name">${platform.charAt(0).toUpperCase() + platform.slice(1)}</span>
        <div class="stats-info">
            <span class="platform-percentage">${percentage}%</span>
            <span class="platform-count">(${formatNumber(count)})</span>
        </div>
    `;
    return div;
} 