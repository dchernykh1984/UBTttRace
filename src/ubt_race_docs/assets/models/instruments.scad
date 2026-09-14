// Брендирование готовых инструментов гонки.
//
// Форму этих инструментов рисовали не мы — мы только гравируем на них гонку,
// эмблему команды и логотип партнёра. Сами модели лежат в `vendor/`, их
// источники и лицензии перечислены в `vendor/README.md`.
//
//   chain-wear — измеритель растяжения цепи (планка 159 × 33 × 2 мм);
//   cassette   — скребок для чистки между звёздами кассеты (221 × 48 × 4 мм).
//
// Гравировка мелкая и лежит на плоских участках вдали от рабочих кромок:
// у измерителя это щупы на торцах, у скребка — зубья по краям.
//
//   openscad -o chain-wear.stl -D 'part="chain-wear"' instruments.scad

/* [Что печатать] */
part = "chain-wear"; // [chain-wear, cassette]

/* [Надписи] */
title_line = "UBT TT · 04.10.2026";
role_line = "Участник · Қатысушы";
font_name = "DejaVu Sans:style=Bold";
logo_file = "ubt-logo.svg";
giant_file = "giant-logo.svg";
logo_source_height = 116.1;
giant_source_width = 99.81;

/* [Измеритель растяжения цепи] */
// Планка 2 мм толщиной: гравируем на 0.4, под надписью остаётся 1.6 мм.
chain_file = "vendor/chain-wear-indicator.stl";
chain_thickness = 2;
chain_engrave = 0.4;
// Планка ровная от Y = 8 до Y = 27, поэтому всё идёт по её середине.
chain_text_size = 4.0;
chain_text_at = [68, 17.5];
chain_logo_at = [22, 17.5];
chain_logo_height = 13;
chain_giant_at = [118, 17.5];
chain_giant_width = 22;

/* [Скребок кассеты] */
// Гравируем ОБРАТНУЮ сторону: лицевую занимает авторская «Tooth Tool v2»,
// поверх неё буквы не отпечатываются и всё превращается в кашу. Сзади
// пластина чистая, и надписи ложатся так же, как на медали.
cassette_file = "vendor/cassette-cleaner.stl";
cassette_thickness = 4;
cassette_engrave = 0.5;
// Тот же порядок, что и на планке измерителя: эмблема, надписи, партнёр.
// Деталь сужается наискось, её середина уходит вниз на 8.4°, поэтому
// элементы стоят не на одной высоте, а каждый по своей середине — и весь
// блок повёрнут вдоль детали. Читается блок с обратной стороны, поэтому
// в модели порядок обратный: партнёр слева, эмблема справа.
cassette_text_size = 3.0;
cassette_angle = -8.4;
cassette_giant_at = [12, -1.0];
cassette_giant_width = 18;
cassette_title_at = [50, -2.5];
cassette_role_at = [50, -7.5];
cassette_logo_at = [82.5, -12];
cassette_logo_height = 10;

$fn = 48;


module engraved_text(line, size) {
    linear_extrude(height = 10)
        text(line, font = font_name, size = size, halign = "center", valign = "center");
}

module ubt_logo(height) {
    $fn = 12;
    linear_extrude(height = 10)
        scale(height / logo_source_height)
            import(logo_file, center = true);
}

module giant_logo(width) {
    $fn = 12;
    linear_extrude(height = 10)
        scale(width / giant_source_width)
            import(giant_file, center = true);
}

module chain_wear_indicator() {
    difference() {
        import(chain_file);
        translate([0, 0, chain_thickness - chain_engrave]) {
            translate(chain_text_at) engraved_text(title_line, chain_text_size);
            translate(chain_logo_at) ubt_logo(chain_logo_height);
            translate(chain_giant_at) giant_logo(chain_giant_width);
        }
    }
}

// Обратная сторона смотрит вниз, поэтому каждый элемент зеркалим на месте:
// иначе на готовой детали надписи читались бы наоборот.
module back_engraving() {
    translate([0, 0, -10 + cassette_engrave])
        linear_extrude(height = 10)
            children();
}

module cassette_cleaner() {
    difference() {
        import(cassette_file);
        translate(cassette_logo_at) rotate([0, 0, cassette_angle]) back_engraving()
            mirror([1, 0, 0]) scale(cassette_logo_height / logo_source_height)
                import(logo_file, center = true, $fn = 12);
        translate(cassette_title_at) rotate([0, 0, cassette_angle]) back_engraving()
            mirror([1, 0, 0]) text(title_line, font = font_name, size = cassette_text_size,
                                   halign = "center", valign = "center");
        translate(cassette_role_at) rotate([0, 0, cassette_angle]) back_engraving()
            mirror([1, 0, 0]) text(role_line, font = font_name, size = cassette_text_size,
                                   halign = "center", valign = "center");
        translate(cassette_giant_at) rotate([0, 0, cassette_angle]) back_engraving()
            mirror([1, 0, 0]) scale(cassette_giant_width / giant_source_width)
                import(giant_file, center = true, $fn = 12);
    }
}

if (part == "chain-wear") chain_wear_indicator();
else if (part == "cassette") cassette_cleaner();
else assert(false, "part должен быть chain-wear или cassette");
