// Медаль участника UBT TT — сувенир, который остаётся инструментом.
//
// Три исполнения, одинаковые снаружи:
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
//   openscad -o medal-key.stl -D 'part="key"' medal.scad

/* [Что печатать] */
part = "key"; // [key, whistle, dog-whistle]

/* [Надписи] */
title_line = "UBT TT · 04.10.2026";
role_line = "Участник · Қатысушы";
font_name = "DejaVu Sans:style=Bold";
logo_file = "ubt-logo.svg";
giant_file = "giant-logo.svg";
// Ширина обоих контуров в файлах — 100 единиц, высота у каждого своя.
logo_source_height = 116.1;
giant_source_width = 99.81;

text_size = 2.4;
logo_y = 14;
title_y = 4;
role_y = -3.5;
giant_y = -13;
engrave_depth = 0.6;
logo_height = 12;
giant_width = 18;

/* [Медаль] */
medal_diameter = 50;
medal_thickness = 5;
edge_chamfer = 0.7;
lanyard_hole = 4;
lanyard_margin = 4.5;

mark_size = 2.2;

/* [Ключ крышки шатуна] */
// Крышка натяга Hollowtech II имеет ВНУТРЕННИЕ шлицы, поэтому ключ — это
// торчащий из медали зубчатый выступ, а медаль служит рукояткой. Число
// зубцов и пропорции сняты с фотографии заводского инструмента: десять
// широких округлых зубцов, между ними узкие неглубокие впадины.
cap_points = 10;
cap_outer_diameter = 16.0;
cap_groove_width = 2.4;
cap_groove_depth = 0.6;
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
whistle_line = ["WHISTLE"];
dog_line = ["ANTI-DOG", "WHISTLE"];

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

// Медальная раскладка сверху вниз: эмблема команды, гонка, кого награждаем,
// партнёр. С эмблемы начинать правильнее, а строки уходят ближе к середине,
// где хорда длиннее — там они не упираются в кромку и набраны крупнее.
module face_engraving() {
    face_plate() {
        translate([0, logo_y, 0]) ubt_logo(logo_height);
        engraved_text(title_line, text_size, title_y);
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
        for (index = [0 : len(line) - 1])
            translate([0, 17 - index * 3.4, medal_thickness - engrave_depth])
                linear_extrude(height = engrave_depth * 2)
                    text(line[index], font = font_name, size = mark_size,
                         halign = "center", valign = "center");
    }
}

if (part == "key") key_medal();
else if (part == "whistle")
    whistle_medal(whistle_chamber_diameter, whistle_chamber_height, whistle_line);
else if (part == "dog-whistle")
    whistle_medal(dog_chamber_diameter, dog_chamber_height, dog_line);
else assert(false, "part должен быть key, whistle или dog-whistle");
