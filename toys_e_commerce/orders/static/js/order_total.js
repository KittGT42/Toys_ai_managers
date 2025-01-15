(function($) {
    $(document).ready(function() {
        function updateTotalPrice() {
            var total = 0;
            $('.field-quantity input').each(function() {
                var quantity = parseInt($(this).val()) || 0;
                var row = $(this).closest('tr');
                var priceData = row.data('product-price');
                if (priceData) {
                    total += quantity * parseFloat(priceData);
                }
            });
            $('#id_total_price').val(total.toFixed(2));
        }

        // Оновлення при зміні кількості
        $(document).on('change', '.field-quantity input', updateTotalPrice);

        // Додавання data-атрибуту з ціною до рядків
        function initializePrices(row) {
            row.find('.field-product select').each(function() {
                var productId = $(this).val();
                if (productId) {
                    $.get('/admin/api/product-price/' + productId, function(data) {
                        row.data('product-price', data.price);
                    });
                }
            });
        }

        // Инициализация цен при загрузке страницы
        $('.field-quantity input').each(function() {
            initializePrices($(this).closest('tr'));
        });

        // Инициализация для новых строк
        $(document).on('formset:added', function(event, $row, formsetName) {
            initializePrices($row);
            $row.find('.field-quantity input').on('change', updateTotalPrice);
        });
    });
})(django.jQuery);
