// Медаль участника UBT TT — сувенир, который остаётся инструментом.
//
// Три исполнения, одинаковые снаружи:
//   spacer  — транспортные проставки под колодки: одна кромка под Shimano,
//             противоположная под SRAM;
//   key     — ключ для пластиковой крышки предварительного натяга Shimano
//             Hollowtech II (та самая, что TL-FC16);
//   whistle — свисток, чтобы отгонять собак.
//
// Лицевая сторона у всех одна и та же и лежит ВНИЗУ: медаль печатается
// гравировкой на стол. Так надписи выходят чёткими (первый слой прижат
// к плите), а функциональная сторона со ступеньками и полостями смотрит
// вверх и печатается без единой поддержки.
//
//   openscad -o medal-spacer.stl -D 'part="spacer"' medal.scad

/* [Что печатать] */
part = "spacer"; // [spacer, key, whistle]

/* [Надписи] */
title_line = "UBT TT · 04.10.2026";
role_line = "Участник · Қатысушы";
font_name = "DejaVu Sans:style=Bold";
logo_file = "ubt-logo.svg";
giant_file = "giant-logo.svg";
// Ширина обоих контуров в файлах — 100 единиц, высота у каждого своя.
logo_source_height = 116.1;
giant_source_width = 99.81;

text_size = 2.1;
title_y = 16;
role_y = 12.6;
engrave_depth = 0.6;
logo_height = 10;
giant_width = 16;

/* [Медаль] */
medal_diameter = 50;
medal_thickness = 5;
edge_chamfer = 0.7;
lanyard_hole = 4;
lanyard_margin = 4.5;

/* [Проставки под колодки] */
// Толщины взяты у штатных проставок: Shimano кладёт 1.8 мм, SRAM для
// шоссейных Red/Force/Rival AXS — 2.8 мм. Проверять на своих тормозах.
shimano_thickness = 1.8;
sram_thickness = 2.8;
// Рабочая зона — клиновидный сектор: он расширяется к кромке, поэтому
// заходит между колодок на всю глубину, а не упирается плечами.
spacer_angle = 54;
spacer_label_size = 2.4;
spacer_label_radius = 19;
spacer_label_depth = 0.35;

/* [Ключ крышки шатуна] */
// Крышка предварительного натяга Hollowtech II — восьмилучевая звезда.
// Размеры под проверку штангенциркулем: правится здесь одной строкой.
cap_points = 8;
cap_diameter = 21.6;
cap_tooth_depth = 1.5;
cap_tooth_width = 3.4;
cap_clearance = 0.25;

/* [Свисток] */
// Резонатор Гельмгольца: объём камеры и сечение окна задают тон. При этих
// числах выходит около 7–8 кГц — человеку пронзительно, собаке отлично
// слышно. Настоящий ультразвук на FDM не выдуть: каналы нужны глаже.
whistle_chamber_diameter = 11;
whistle_chamber_height = 2.6;
whistle_window = 4.2;
whistle_channel_height = 1.2;
whistle_channel_width = 4.2;
whistle_wall = 1.4;
whistle_line = "ANTI-DOG WHISTLE";

$fn = 64;


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

// Центр медали занят инструментом — у ключа там и вовсе сквозное гнездо, —
// поэтому надписи уходят вверх, логотипы вниз, а середина остаётся пустой.
module face_engraving() {
    face_plate() {
        engraved_text(title_line, text_size, title_y);
        engraved_text(role_line, text_size, role_y);
        translate([-10, -15, 0]) ubt_logo(logo_height);
        translate([10, -15.5, 0]) giant_logo(giant_width);
    }
}

module lanyard() {
    offset = medal_diameter / 2 - lanyard_margin;
    translate([offset, 0, -1]) cylinder(d = lanyard_hole, h = medal_thickness + 2);
}

// Кромка, сточенная до толщины проставки. Сектор вырезается с верхней
// стороны — при печати это ступенька, а не нависание.
module spacer_cut(thickness, direction) {
    reach = medal_diameter;
    rotate([0, 0, direction])
        translate([0, 0, thickness])
            linear_extrude(height = medal_thickness)
                polygon([
                    [0, 0],
                    [reach * sin(-spacer_angle / 2), reach * cos(spacer_angle / 2)],
                    [reach * sin(spacer_angle / 2), reach * cos(spacer_angle / 2)],
                ]);
}

// Подпись лежит на самом сточенном секторе, поэтому гравируем мельче:
// под ней остаётся только толщина проставки.
module spacer_label(line, thickness, direction) {
    rotate([0, 0, direction])
        translate([0, spacer_label_radius, thickness - spacer_label_depth])
            rotate([0, 0, direction == 0 ? 0 : 180])
                linear_extrude(height = spacer_label_depth * 2)
                    text(line, font = font_name, size = spacer_label_size,
                         halign = "center", valign = "center");
}

module spacer_medal() {
    difference() {
        medal_blank();
        face_engraving();
        lanyard();
        spacer_cut(shimano_thickness, 0);
        spacer_cut(sram_thickness, 180);
        spacer_label("SHIMANO 1.8", shimano_thickness, 0);
        spacer_label("SRAM 2.8", sram_thickness, 180);
    }
}

// Гнездо под крышку: цилиндр по её диаметру плюс пазы под лучи звезды.
module cap_socket() {
    radius = (cap_diameter + cap_clearance) / 2;
    translate([0, 0, -1]) cylinder(r = radius, h = medal_thickness + 2);
    for (index = [0 : cap_points - 1])
        rotate([0, 0, index * 360 / cap_points])
            translate([-cap_tooth_width / 2, radius - 0.1, -1])
                cube([cap_tooth_width, cap_tooth_depth + 0.1, medal_thickness + 2]);
}

module key_medal() {
    difference() {
        medal_blank();
        face_engraving();
        lanyard();
        cap_socket();
    }
}

// Свисток: воздух заходит с кромки узким каналом, разбивается об острую
// кромку окна и раскачивает закрытую камеру за ним.
module whistle_void() {
    radius = medal_diameter / 2;
    z = whistle_wall;
    // канал вдува от кромки внутрь
    translate([-whistle_channel_width / 2, -radius - 1, z])
        cube([whistle_channel_width, radius - whistle_chamber_diameter / 2 + 1,
              whistle_channel_height]);
    // окно наружу: через него уходит струя и звучит свисток
    translate([-whistle_window / 2, -whistle_chamber_diameter / 2 - whistle_window, z])
        cube([whistle_window, whistle_window, medal_thickness]);
    // резонансная камера
    translate([0, 0, z]) cylinder(d = whistle_chamber_diameter, h = whistle_chamber_height);
}

module whistle_medal() {
    difference() {
        medal_blank();
        face_engraving();
        lanyard();
        whistle_void();
        translate([0, 15, medal_thickness - engrave_depth])
            linear_extrude(height = engrave_depth * 2)
                text(whistle_line, font = font_name, size = spacer_label_size,
                     halign = "center", valign = "center");
    }
}

if (part == "spacer") spacer_medal();
else if (part == "key") key_medal();
else if (part == "whistle") whistle_medal();
else assert(false, "part должен быть spacer, key или whistle");
