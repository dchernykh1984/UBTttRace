// Медаль участника UBT TT — сувенир, который остаётся инструментом.
//
// Три исполнения, одинаковые снаружи:
//   spacer      — транспортная проставка под колодки: ступенчатый язычок,
//                 дальняя часть 1.8 мм (Shimano), ближняя 2.8 мм (SRAM);
//   key         — ключ крышки натяга Shimano Hollowtech II: шлицевой выступ,
//                 медаль работает рукояткой;
//   whistle     — свисток;
//   dog-whistle — свисток повыше тоном, чтобы отгонять собак.
//
// Лицевая сторона у всех одна и та же и лежит ВНИЗУ: медаль печатается
// гравировкой на стол. Так надписи выходят чёткими (первый слой прижат
// к плите), а функциональная сторона со ступеньками и полостями смотрит
// вверх и печатается без единой поддержки.
//
//   openscad -o medal-spacer.stl -D 'part="spacer"' medal.scad

/* [Что печатать] */
part = "spacer"; // [spacer, key, whistle, dog-whistle]

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

/* [Проставка под колодки] */
// Толщины взяты у штатных проставок: Shimano кладёт 1.8 мм, SRAM для
// шоссейных Red/Force/Rival AXS — 2.8 мм. Проверять на своих тормозах.
shimano_thickness = 1.8;
sram_thickness = 2.8;
// Проставка заходит в узкую щель для ротора, поэтому это торчащий из медали
// язычок, а не сточенная кромка: кромкой в суппорт не залезть. Язычок
// ступенчатый по длине — тонким концом в Shimano, целиком в SRAM.
spacer_tongue_length = 17;
spacer_tongue_width = 13;
spacer_thin_length = 9;
spacer_label_size = 2.2;
spacer_label_depth = 0.35;

/* [Ключ крышки шатуна] */
// Крышка натяга Hollowtech II имеет ВНУТРЕННИЕ шлицы, поэтому ключ — это
// торчащий из медали восьмизубый выступ, а медаль служит рукояткой.
// Диаметр снят с чужого инструмента приблизительно: измерьте свой
// штангенциркулем и поправьте здесь.
cap_points = 8;
cap_root_diameter = 14.2;
cap_tooth_height = 1.3;
cap_tooth_width = 3.0;
cap_driver_height = 8;
cap_lead_in = 0.8;

/* [Свисток] */
// Резонатор Гельмгольца: объём камеры и сечение окна задают тон. При этих
// числах выходит около 7–8 кГц — человеку пронзительно, собаке отлично
// слышно. Настоящий ультразвук на FDM не выдуть: каналы нужны глаже.
// Камера побольше звучит ниже и громче, поменьше — пронзительнее.
whistle_chamber_diameter = 24;
whistle_chamber_height = 3;
dog_chamber_diameter = 11;
dog_chamber_height = 2.6;
whistle_window = 4.2;
whistle_channel_height = 1.2;
whistle_channel_width = 4.2;
whistle_wall = 1.4;
whistle_line = "WHISTLE";
dog_line = "ANTI-DOG WHISTLE";

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

// Язычок проставки: торчит из кромки медали и входит в щель для ротора.
// Ступенька по длине даёт обе ходовые толщины одной деталью — тонкий конец
// для Shimano, весь язычок целиком для SRAM.
module spacer_tongue() {
    radius = medal_diameter / 2;
    base = radius - 3;
    thick_length = spacer_tongue_length - spacer_thin_length;
    // толстая часть у самой медали
    translate([-spacer_tongue_width / 2, base, 0])
        cube([spacer_tongue_width, thick_length + 3, sram_thickness]);
    // тонкий конец со скруглением: так он находит щель наощупь
    hull() {
        translate([-spacer_tongue_width / 2, base + thick_length, 0])
            cube([spacer_tongue_width, 0.1, shimano_thickness]);
        translate([0, base + thick_length + spacer_thin_length - spacer_tongue_width / 2, 0])
            cylinder(d = spacer_tongue_width, h = shimano_thickness);
    }
}

module spacer_marks() {
    radius = medal_diameter / 2;
    base = radius - 3;
    thick_length = spacer_tongue_length - spacer_thin_length;
    translate([0, base + thick_length / 2, sram_thickness - spacer_label_depth])
        linear_extrude(height = spacer_label_depth * 2)
            text("2.8", font = font_name, size = spacer_label_size,
                 halign = "center", valign = "center");
    translate([0, base + thick_length + 3, shimano_thickness - spacer_label_depth])
        linear_extrude(height = spacer_label_depth * 2)
            text("1.8", font = font_name, size = spacer_label_size,
                 halign = "center", valign = "center");
    translate([0, 8, medal_thickness - engrave_depth])
        linear_extrude(height = engrave_depth * 2)
            text("SRAM 2.8 · SHIMANO 1.8", font = font_name, size = spacer_label_size,
                 halign = "center", valign = "center");
}

module spacer_medal() {
    difference() {
        union() {
            medal_blank();
            spacer_tongue();
        }
        face_engraving();
        lanyard();
        spacer_marks();
    }
}

// Ключ: шлицевой выступ под внутренние зубцы крышки натяга. Печатается
// стоймя вместе с медалью, поэтому обходится без поддержек.
module cap_driver() {
    root = cap_root_diameter;
    translate([0, 0, medal_thickness]) {
        cylinder(d = root, h = cap_driver_height);
        for (index = [0 : cap_points - 1])
            rotate([0, 0, index * 360 / cap_points])
                hull() {
                    translate([-cap_tooth_width / 2, root / 2 - 0.6, 0])
                        cube([cap_tooth_width, cap_tooth_height + 0.6, 0.1]);
                    translate([-cap_tooth_width / 2, root / 2 - 0.6, cap_driver_height - cap_lead_in])
                        cube([cap_tooth_width, cap_tooth_height + 0.6, cap_lead_in]);
                }
    }
}

module key_medal() {
    difference() {
        union() {
            medal_blank();
            cap_driver();
        }
        face_engraving();
        lanyard();
    }
}

// Свисток: воздух заходит с кромки узким каналом, разбивается об острую
// кромку окна и раскачивает закрытую камеру за ним.
module whistle_void(chamber_diameter, chamber_height) {
    radius = medal_diameter / 2;
    z = whistle_wall;
    translate([-whistle_channel_width / 2, -radius - 1, z])
        cube([whistle_channel_width, radius - chamber_diameter / 2 + 1, whistle_channel_height]);
    translate([-whistle_window / 2, -chamber_diameter / 2 - whistle_window, z])
        cube([whistle_window, whistle_window, medal_thickness]);
    translate([0, 0, z]) cylinder(d = chamber_diameter, h = chamber_height);
}

module whistle_medal(chamber_diameter, chamber_height, line) {
    difference() {
        medal_blank();
        face_engraving();
        lanyard();
        whistle_void(chamber_diameter, chamber_height);
        translate([0, medal_diameter / 2 - 6, medal_thickness - engrave_depth])
            linear_extrude(height = engrave_depth * 2)
                text(line, font = font_name, size = spacer_label_size,
                     halign = "center", valign = "center");
    }
}

if (part == "spacer") spacer_medal();
else if (part == "key") key_medal();
else if (part == "whistle")
    whistle_medal(whistle_chamber_diameter, whistle_chamber_height, whistle_line);
else if (part == "dog-whistle")
    whistle_medal(dog_chamber_diameter, dog_chamber_height, dog_line);
else assert(false, "part должен быть spacer, key, whistle или dog-whistle");
