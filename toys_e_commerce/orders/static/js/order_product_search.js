(function($) {
    $(document).ready(function() {
        // Функція для відкриття popup вікна пошуку
        window.showProductPopup = function(productId) {
            var url = '/admin/products/product/?';
            if (productId) {
                url += '_popup=1&id=' + productId;
            } else {
                url += '_popup=1';
            }
            window.open(url, 'ProductSearch', 'height=500,width=800,resizable=yes,scrollbars=yes');
            return false;
        };

        // Модифікуємо поведінку кнопки додавання
        $('.add-row a').click(function(e) {
            e.preventDefault();
            showProductPopup();
        });

        // Функція для оновлення даних про продукт після вибору
        window.updateProduct = function(productId, articleNumber, name, price) {
            var row = $(this).closest('tr');
            row.find('.field-get_article').text(articleNumber);
            row.find('.field-get_name').text(name);
            row.find('.field-get_price').text(price + ' грн');
            row.find('input[name$="-product"]').val(productId);
            updateTotalPrice();
        };
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
    }

    // Оновлення при зміні кількості
    $(document).on('change', '.field-quantity input', updateTotalPrice);
})(django.jQuery);