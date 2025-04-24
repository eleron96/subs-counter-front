document.addEventListener('DOMContentLoaded', () => {
    // Получаем данные о подписчиках для LinkedIn, YouTube, Medium и Instagram из скрытых элементов
    let linkedinCount = parseInt(document.getElementById('linkedin_count').textContent.replace(/,/g, ''), 10) || 0;
    let youtubeCount = parseInt(document.getElementById('youtube_count').textContent, 10) || 0;
    let mediumCount = parseInt(document.getElementById('medium_count').textContent, 10) || 0;
    let instagramCount = parseInt(document.getElementById('instagram_count').textContent, 10) || 0;

    // Получаем даты через data-атрибуты
    let linkedinTimestamp = document.getElementById('linkedin-last-updated').dataset.timestamp;
    let youtubeTimestamp = document.getElementById('youtube-last-updated').dataset.timestamp;
    let mediumTimestamp = document.getElementById('medium-last-updated').dataset.timestamp;
    let instagramTimestamp = document.getElementById('instagram-last-updated').dataset.timestamp;

    console.log('LinkedIn Timestamp:', linkedinTimestamp);
    console.log('YouTube Timestamp:', youtubeTimestamp);
    console.log('Medium Timestamp:', mediumTimestamp);
    console.log('Instagram Timestamp:', instagramTimestamp);

    // Функция для анимации прокрутки до нужного значения
    function animateFlipClock(element, targetCount) {
        const digits = element.querySelectorAll('.digit');
        let currentCount = 0; // Начальное значение
        const totalDigits = digits.length;

        const duration = 2000; // 2 секунды
        const intervalTime = 20; // обновление цифр каждое 20мс
        const steps = duration / intervalTime;
        const stepValue = (targetCount - currentCount) / steps;

        const interval = setInterval(() => {
            currentCount += stepValue;
            const valueString = Math.round(currentCount).toString().padStart(totalDigits, '0');

            valueString.split('').forEach((digit, index) => {
                const digitElement = digits[index];
                digitElement.textContent = digit;
            });

            if (Math.abs(currentCount - targetCount) < 0.5) {
                clearInterval(interval); // Завершаем анимацию, когда значение близко к целевому
            }
        }, intervalTime);
    }

    // Функция для преобразования строки даты в правильный формат с учетом часового пояса пользователя
    function formatTime(timestamp) {
        console.log("Исходная дата, переданная в JavaScript:", timestamp); // Логируем исходную дату

        // Преобразуем строку в формат YYYY-MM-DDTHH:MM:SS
        const regex = /(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})\.(\d{6})/;
        const match = timestamp.match(regex);

        if (!match) {
            console.error("Не удалось обработать дату:", timestamp);
            return "Некорректная дата";
        }

        // Логируем результат работы регулярного выражения
        console.log("Результат работы регулярного выражения:", match);

        // Формируем строку ISO
        const isoDate = `${match[1]}-${match[2]}-${match[3]}T${match[4]}:${match[5]}:${match[6]}`;
        console.log("Преобразованная дата в ISO:", isoDate); // Логируем преобразованную дату в ISO

        const dateObj = new Date(isoDate);

        // Логируем результат преобразования в объект Date
        console.log("Объект Date:", dateObj);

        if (isNaN(dateObj.getTime())) {
            console.error("Невалидная дата:", timestamp);
            return "Некорректная дата";
        }

        // Добавляем 3 часа к времени (например, если пользователь в Москве)
        dateObj.setHours(dateObj.getHours() + 3);  // Добавляем 3 часа к времени UTC (GMT)

        // Форматируем в нужный вид: 26 фев 2025, 09:37
        const options = {
            year: 'numeric',
            month: 'short',  // 'short' дает нам аббревиатуру месяца
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };

        return dateObj.toLocaleString('ru-RU', options).replace(',', ''); // Убираем запятую между датой и временем
    }

    // Инициализируем анимацию для каждого элемента
    animateFlipClock(document.getElementById('linkedin-clock'), linkedinCount);
    animateFlipClock(document.getElementById('youtube-clock'), youtubeCount);
    animateFlipClock(document.getElementById('medium-clock'), mediumCount);
    animateFlipClock(document.getElementById('instagram-clock'), instagramCount);

    // Получаем и форматируем дату с учетом часового пояса
    document.getElementById('linkedin-last-updated').textContent = formatTime(linkedinTimestamp);
    document.getElementById('youtube-last-updated').textContent = formatTime(youtubeTimestamp);
    document.getElementById('medium-last-updated').textContent = formatTime(mediumTimestamp);
    document.getElementById('instagram-last-updated').textContent = formatTime(instagramTimestamp);
});


