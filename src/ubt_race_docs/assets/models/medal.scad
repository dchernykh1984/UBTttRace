// Медаль участника UBT TT — сувенир, который остаётся инструментом.
//
// Три исполнения, одинаковые снаружи:
//   key         — ключ крышки натяга Shimano Hollowtech II: шлицевой выступ,
//                 медаль работает рукояткой;
//   jockey      — скребок ролика заднего переключателя: прорезь по кромке,
//                 в неё заходит зуб ролика и очищается с обеих сторон;
//
// Лицевая сторона у всех одна и та же и лежит ВНИЗУ: медаль печатается
// гравировкой на стол. Так надписи выходят чёткими (первый слой прижат
// к плите), а функциональная сторона со ступеньками и полостями смотрит
// вверх и печатается без единой поддержки.
//
//   openscad -o medal-key.stl -D 'part="key"' medal.scad

/* [Что печатать] */
part = "key"; // [key, jockey]

/* [Надписи] */
title_line = "UBT TT · 04.10.2026";
role_line = "Участник · Қатысушы";
font_name = "DejaVu Sans:style=Bold";
logo_file = "ubt-logo.svg";
giant_file = "giant-logo.svg";
// Ширина обоих контуров в файлах — 100 единиц, высота у каждого своя.
logo_source_height = 116.1;
giant_source_width = 99.81;

// Гравировка ложится на первый слой, а он при печати расплющивается:
// мелкие буквы заплывают. Поэтому шрифт крупный, а глубина — миллиметр.
// Размеры подобраны перебором: всё максимально крупное, что влезает в круг
// с отступом 2 мм от кромки и зазорами 1.5 мм между элементами.
text_size = 3.3;
title_extra = 0.3;
logo_y = 16.9;
title_y = 3.2;
role_y = -3.0;
giant_y = -11.1;
engrave_depth = 1.0;
logo_height = 19.5;
giant_width = 46;

/* [Медаль] */
medal_diameter = 60;
medal_thickness = 5;
edge_chamfer = 0.7;
lanyard_hole = 4;
lanyard_margin = 5;

mark_size = 2.2;

/* [Ключ крышки шатуна] */
// Крышка натяга Hollowtech II имеет ВНУТРЕННИЕ шлицы, поэтому ключ — это
// торчащий из медали зубчатый выступ, а медаль служит рукояткой. Число
// зубцов и размеры сняты сечениями с готовых моделей настоящих ключей:
// вершины ⌀15.3–15.5, впадины глубиной 1.0–1.8 мм, зубцов восемь.
cap_points = 8;
cap_outer_diameter = 15.4;
cap_groove_width = 3.8;
cap_groove_depth = 1.5;
cap_driver_height = 8;
cap_lead_in = 0.8;
// Рифление по кромке: за медаль держатся пальцами и крутят ею крышку.
// Шаг взят у заводского ключа — там 33 ребра на диаметре 40 мм.
knurl_teeth = 50;
knurl_groove = 2.0;
knurl_depth = 0.7;

/* [Скребок ролика] */
// Прорезь по кромке медали: в неё входит зуб ролика, стенки счищают грязь
// с его боков, а мелкие выемки рядом достают до впадин между зубьями.
// Размеры сняты с готового скребка под 12-скоростную цепь.
jockey_slot_width = 2.9;
jockey_slot_depth = 8;
jockey_notch = 1.4;
jockey_notch_width = 2.6;
jockey_notch_gap = 5.5;
// Рабочую кромку стачиваем: пятимиллиметровым диском между щёчками рамки
// переключателя не подлезть.
jockey_edge_thickness = 1.6;
jockey_edge_reach = 13;
// Прорезь уводим на свободную диагональ: сверху она развалила бы эмблему,
// а по горизонтали перерезала бы строки.
jockey_direction = 135;
// Подпись на трёх языках. Казахскую строку должен вычитать носитель.
jockey_line = ["JOCKEY SCRAPER", "Очиститель ролика", "Ролик тазалағышы"];
jockey_label_size = 3.7;
jockey_label_step = 6.2;
// Подпись уходит на целую половину медали: на сточенной кромке под ней
// остаётся полтора миллиметра, и буквы проваливаются в прорезь.
jockey_label_radius = 8.7;

$fn = 64;


// Рифление по кромке — только у ключа: этой медалью крутят крышку шатуна,
// и пальцы не должны проскальзывать. Шаг взят у заводского инструмента.
module knurled_rim() {
    radius = medal_diameter / 2;
    for (index = [0 : knurl_teeth - 1])
        rotate([0, 0, index * 360 / knurl_teeth])
            translate([0, radius + knurl_groove / 2 - knurl_depth, -1])
                cylinder(d = knurl_groove, h = medal_thickness + 2, $fn = 16);
}

module medal_blank() {
    radius = medal_diameter / 2;
    // Фаска с обеих сторон: и в руке приятнее, и первый слой не заваливается.
    hull() {
        cylinder(r = radius - edge_chamfer, h = medal_thickness);
        translate([0, 0, edge_chamfer])
            cylinder(r = radius, h = medal_thickness - 2 * edge_chamfer);
    }
}

// Лицевая сторона смотрит вниз, поэтому всё на ней зеркалим: иначе надписи
// на готовой медали читались бы наоборот.
module face_plate() {
    mirror([1, 0, 0]) children();
}

module engraved_text(line, size, y) {
    translate([0, y, 0])
        linear_extrude(height = engrave_depth * 2, center = true)
            text(line, font = font_name, size = size, halign = "center", valign = "center");
}

// Логотипы на медали мелкие, и полная гранёность контуров раздувала бы STL
// до десятка мегабайт — на столе их лежит два десятка разом.
module ubt_logo(height) {
    $fn = 12;
    linear_extrude(height = engrave_depth * 2, center = true)
        scale(height / logo_source_height)
            import(logo_file, center = true);
}

module giant_logo(width) {
    $fn = 12;
    linear_extrude(height = engrave_depth * 2, center = true)
        scale(width / giant_source_width)
            import(giant_file, center = true);
}

// Медальная раскладка сверху вниз: эмблема команды, гонка, кого награждаем,
// партнёр. С эмблемы начинать правильнее, а строки уходят ближе к середине,
// где хорда длиннее — там они не упираются в кромку и набраны крупнее.
module face_engraving() {
    face_plate() {
        translate([0, logo_y, 0]) ubt_logo(logo_height);
        engraved_text(title_line, text_size + title_extra, title_y);
        engraved_text(role_line, text_size, role_y);
        translate([0, giant_y, 0]) giant_logo(giant_width);
    }
}

// Отверстие уводим к плечу медали: по горизонтали оно упиралось бы в строки,
// а сверху — в эмблему.
module lanyard() {
    offset = medal_diameter / 2 - lanyard_margin;
    translate([offset * cos(45), offset * sin(45), -1])
        cylinder(d = lanyard_hole, h = medal_thickness + 2);
}

// Ключ: шлицевой выступ под внутренние зубцы крышки натяга. Печатается
// стоймя вместе с медалью, поэтому обходится без поддержек.
module cap_driver() {
    outer = cap_outer_diameter;
    translate([0, 0, medal_thickness])
        intersection() {
            difference() {
                cylinder(d = outer, h = cap_driver_height);
                // Впадины узкие и круглые, зубцы между ними широкие — так же,
                // как у заводского ключа: широкий зуб не срезает пазы крышки.
                // Канавка мелкая: её окружность отодвинута наружу так, чтобы
                // в тело зашла только глубина cap_groove_depth.
                for (index = [0 : cap_points - 1])
                    rotate([0, 0, index * 360 / cap_points])
                        translate([0, outer / 2 + cap_groove_width / 2 - cap_groove_depth, -1])
                            cylinder(d = cap_groove_width, h = cap_driver_height + 2, $fn = 32);
            }
            // заходное сужение: без него ключ приходится ловить вслепую
            cylinder(d1 = outer + 2, d2 = outer - 2 * cap_lead_in, h = cap_driver_height);
        }
}

module key_medal() {
    difference() {
        union() {
            medal_blank();
            cap_driver();
        }
        knurled_rim();
        face_engraving();
        lanyard();
    }
}

// Сектор кромки, сточенный до рабочей толщины: ступенька смотрит вверх,
// поэтому печатается без поддержек.
module jockey_thin_edge() {
    radius = medal_diameter / 2;
    rotate([0, 0, jockey_direction])
    translate([0, 0, jockey_edge_thickness])
        linear_extrude(height = medal_thickness)
            polygon([
                [0, radius - jockey_edge_reach],
                [-radius, radius - jockey_edge_reach],
                [-radius, radius + 1],
                [radius, radius + 1],
                [radius, radius - jockey_edge_reach],
            ]);
}

module jockey_slots() {
    radius = medal_diameter / 2;
    rotate([0, 0, jockey_direction]) {
    translate([-jockey_slot_width / 2, radius - jockey_slot_depth, -1])
        cube([jockey_slot_width, jockey_slot_depth + 2, medal_thickness + 2]);
    for (side = [-1, 1])
        translate([side * jockey_notch_gap - jockey_notch_width / 2, radius - jockey_notch, -1])
            cube([jockey_notch_width, jockey_notch + 2, medal_thickness + 2]);
    }
}

module jockey_medal() {
    difference() {
        medal_blank();
        face_engraving();
        lanyard();
        jockey_thin_edge();
        jockey_slots();
        rotate([0, 0, jockey_direction + 180])
        for (index = [0 : len(jockey_line) - 1])
            translate([
                0,
                jockey_label_radius - index * jockey_label_step,
                medal_thickness - engrave_depth,
            ])
                linear_extrude(height = engrave_depth * 2)
                    text(jockey_line[index], font = font_name, size = jockey_label_size,
                         halign = "center", valign = "center");
    }
}

module whistle_medal(chamber_diameter, chamber_height, line) {
    difference() {
        medal_blank();
        face_engraving();
        lanyard();
        whistle_void(chamber_diameter, chamber_height);
        for (index = [0 : len(line) - 1])
            translate([0, 17 - index * 3.4, medal_thickness - engrave_depth])
                linear_extrude(height = engrave_depth * 2)
                    text(line[index], font = font_name, size = mark_size,
                         halign = "center", valign = "center");
    }
}

if (part == "key") key_medal();
else if (part == "jockey") jockey_medal();
else assert(false, "part должен быть key или jockey");
