// Инструменты гонки: измеритель растяжения цепи и скребок кассеты.
//
//   chain-wear — наш измеритель растяжения цепи (145 × 44 × 6 мм);
//   cassette   — скребок для чистки между звёздами кассеты (221 × 48 × 4 мм),
//                модель чужая, лежит в `vendor/`, лицензия в `vendor/README.md`.
//
// Измеритель мы рисуем сами: готовые модели, которые нашлись, либо тонкие
// и гнутся в руках, либо выложены под некоммерческой лицензией. Геометрия
// у такого инструмента всё равно продиктована цепью, а не автором.
//
// Гравировка мелкая и лежит на плоских участках вдали от рабочих кромок:
// у измерителя это щупы по кромкам, у скребка — зубья по краям.
//
//   openscad -o chain-wear.stl -D 'part="chain-wear"' instruments.scad

/* [Что печатать] */
part = "chain-wear"; // [chain-wear, cassette]

/* [Надписи] */
title_line = "UBT TT · 04.10.2026";
role_line = "Участник · Қатысушы";
font_name = "DejaVu Sans:style=Bold";
giant_file = "giant-logo.svg";
giant_source_width = 99.81;

/* [Измеритель растяжения цепи] */
// Как он меряет. Щупы садятся в просветы между роликами через одиннадцать
// шагов цепи. Расстояние между внешними гранями пары щупов посчитано на
// износ: пролёт = 11 · шаг · (1 + износ) − диаметр ролика. Пока цепь не
// вытянулась до этой цифры, дальний щуп не попадает в просвет и встаёт
// на ролик — инструмент виснет криво. Сел на место — цепь пора менять.
// По одной кромке 0.5 % (11 и 12 скоростей), по другой 1.0 % (до восьми).
// Одиннадцать шагов взяты не случайно: так оба щупа попадают в просветы
// одинакового вида — либо оба между внутренними пластинами, либо оба
// между внешними.
chain_pitch = 12.7;
chain_roller = 7.75;
chain_links = 11;
chain_marks = [0.5, 1.0];
chain_mark_line = ["0,5 %", "1,0 %"];
// Щуп: 2 мм толщиной — пролезает между внутренними пластинами даже
// у 12 скоростей; 4 мм вдоль цепи — входит в просвет 4.95 мм новой цепи.
// Вылет 9 мм: пластины цепи высотой около 11 мм, и щуп должен пройти
// глубже оси ролика, иначе упрётся не в самое широкое место.
chain_tooth = 4;
chain_tooth_thickness = 2;
chain_tooth_reach = 9;
chain_tooth_lead = 1;
// Спинка толстая: старый покупной измеритель был 2 мм и гнулся в руках.
chain_spine = 26;
chain_thickness = 6;
chain_tail = 6;
chain_engrave = 0.6;
// Гравировка по середине спинки: гонка и партнёр. Эмблемы команды тут нет —
// в ней много мелких деталей, и на печати она разбирается в кашу.
chain_text_size = 7.1;
chain_text_at = [52.1, 0];
chain_giant_at = [123.7, 0];
chain_giant_width = 27;
// Проценты стоят у своих щупов, каждый со своей стороны спинки.
chain_mark_size = 4.0;
chain_mark_at = [128.4, 9];

/* [Скребок кассеты] */
// Гравируем ОБРАТНУЮ сторону: лицевую занимает авторская «Tooth Tool v2»,
// поверх неё буквы не отпечатываются и всё превращается в кашу. Сзади
// пластина чистая, и надписи ложатся так же, как на медали.
cassette_file = "vendor/cassette-cleaner.stl";
cassette_thickness = 4;
cassette_engrave = 0.5;
// Порядок тот же, что и на измерителе: гонка, потом партнёр. Эмблемы
// команды тут нет — в ней много мелких деталей, и на печати каша.
// Деталь сужается наискось, её середина уходит вниз, поэтому элементы
// стоят не на одной высоте, а весь блок повёрнут вдоль детали. Читается
// блок с обратной стороны, поэтому в модели порядок обратный: партнёр
// слева, надписи справа.
cassette_text_size = 5.0;
cassette_angle = -6.7;
cassette_giant_at = [-24.0, 0.9];
cassette_giant_width = 31.5;
cassette_title_at = [37.9, 0.0];
cassette_role_at = [37.1, -7.5];

$fn = 48;


module engraved_text(line, size) {
    linear_extrude(height = 10)
        text(line, font = font_name, size = size, halign = "center", valign = "center");
}

module giant_logo(width) {
    $fn = 12;
    linear_extrude(height = 10)
        scale(width / giant_source_width)
            import(giant_file, center = true);
}

// Пролёт между внешними гранями пары щупов для заданного износа в процентах.
function chain_span(wear) = chain_links * chain_pitch * (1 + wear / 100) - chain_roller;

// Щуп: грани вдоль цепи прямые — ими он и упирается в ролики. Сужается
// только кончик, чтобы попадать в просвет, и сужение кончается выше того
// места, где щуп касается роликов.
module chain_tooth_at(x, side) {
    flat = chain_spine / 2 + chain_tooth_reach - chain_tooth_lead;
    tip = chain_spine / 2 + chain_tooth_reach;
    linear_extrude(height = chain_tooth_thickness)
        polygon([
            [x, side * chain_spine / 2],
            [x + chain_tooth, side * chain_spine / 2],
            [x + chain_tooth, side * flat],
            [x + chain_tooth - chain_tooth_lead, side * tip],
            [x + chain_tooth_lead, side * tip],
            [x, side * flat],
        ]);
}

module chain_wear_indicator() {
    length = chain_span(chain_marks[len(chain_marks) - 1]) + 2 * chain_tail;
    difference() {
        union() {
            translate([-chain_tail, -chain_spine / 2, 0])
                cube([length, chain_spine, chain_thickness]);
            for (index = [0 : len(chain_marks) - 1]) {
                side = index == 0 ? 1 : -1;
                chain_tooth_at(0, side);
                chain_tooth_at(chain_span(chain_marks[index]) - chain_tooth, side);
            }
        }
        translate([0, 0, chain_thickness - chain_engrave]) {
            translate(chain_text_at) engraved_text(title_line, chain_text_size);
            translate(chain_giant_at) giant_logo(chain_giant_width);
            for (index = [0 : len(chain_marks) - 1]) {
                side = index == 0 ? 1 : -1;
                translate([chain_mark_at[0], side * chain_mark_at[1]])
                    rotate([0, 0, index == 0 ? 0 : 180])
                        engraved_text(chain_mark_line[index], chain_mark_size);
            }
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
