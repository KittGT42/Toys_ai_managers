(function($) {
    $(document).ready(function() {
        // Отримуємо CSRF токен з cookie
        function getCookie(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
        const csrftoken = getCookie('csrftoken');

        // Додаємо CSRF токен до всіх AJAX запитів
        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            }
        });

        function updateTotalPrice() {
            var total = 0;
            $('.field-quantity input').each(function() {
                var row = $(this).closest('tr');
                var quantity = parseInt($(this).val()) || 0;
                var priceText = row.find('.field-get_price').text();
                var price = parseFloat(priceText.replace(' грн', '')) || 0;
                total += quantity * price;
            });
            $('#id_total_price').val(total.toFixed(2));

            // Відправляємо оновлену суму на сервер
            $.ajax({
                url: window.location.pathname,
                method: 'POST',
                data: {
                    'total_price': total.toFixed(2),
                    'csrfmiddlewaretoken': csrftoken
                },
                success: function(response) {
                    console.log('Total price updated successfully');
                },
                error: function(xhr, status, error) {
                    console.error('Error updating total price:', error);
                }
            });
        }

        // Оновлення при зміні кількості
        $(document).on('change', '.field-quantity input', updateTotalPrice);

        // При зміні вибраного продукту
        $(document).on('change', '.field-product select', function() {
            var row = $(this).closest('tr');
            updateTotalPrice();
        });

        // Оновлення при додаванні нового рядка
        $(document).on('formset:added', function(event, $row, formsetName) {
            $row.find('.field-quantity input').on('change', updateTotalPrice);
            $row.find('.field-product select').on('change', updateTotalPrice);
        });

        // Початкове оновлення
        updateTotalPrice();
    });
})(django.jQuery);

