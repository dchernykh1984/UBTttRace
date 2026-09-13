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

text_size = 1.9;
title_y = 18;
role_y = -4.5;
logo_y = 8;
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

/* [Проставка под колодки] */
// Толщины взяты у штатных проставок: Shimano кладёт 1.8 мм, SRAM для
// шоссейных Red/Force/Rival AXS — 2.8 мм. Проверять на своих тормозах.
shimano_thickness = 1.8;
sram_thickness = 2.8;
// Проставка заходит в узкую щель для ротора, поэтому это торчащий из медали
// язычок, а не сточенная кромка: кромкой в суппорт не залезть. Язычок
// ступенчатый по длине — тонким концом в Shimano, целиком в SRAM.
spacer_tongue_length = 16;
spacer_tongue_width = 13;
spacer_barb = 0.45;
spacer_barb_at = 7;
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

// Медальная раскладка сверху вниз: гонка, эмблема команды, кого награждаем,
// партнёр. Инструмент весь на обратной стороне, поэтому лицо свободно.
module face_engraving() {
    face_plate() {
        engraved_text(title_line, text_size, title_y);
        translate([0, logo_y, 0]) ubt_logo(logo_height);
        engraved_text(role_line, text_size + 0.3, role_y);
        translate([0, giant_y, 0]) giant_logo(giant_width);
    }
}

module lanyard() {
    offset = medal_diameter / 2 - lanyard_margin;
    translate([offset, 0, -1]) cylinder(d = lanyard_hole, h = medal_thickness + 2);
}

// Язычок проставки торчит из кромки медали и входит в щель для ротора.
// Язычков два, в противоположные стороны: тонкий под Shimano, толстый под
// SRAM. Боковые заусенцы держат проставку в суппорте, чтобы она не выпала
// в багажнике: заходят легко, обратно упираются.
module spacer_tongue(thickness, direction) {
    radius = medal_diameter / 2;
    base = radius - 3;
    tip = base + spacer_tongue_length;
    rotate([0, 0, direction]) {
        hull() {
            translate([-spacer_tongue_width / 2, base, 0])
                cube([spacer_tongue_width, 0.1, thickness]);
            translate([0, tip - spacer_tongue_width / 2, 0])
                cylinder(d = spacer_tongue_width, h = thickness, $fn = 48);
        }
        for (side = [-1, 1])
            translate([side * spacer_tongue_width / 2, base + spacer_barb_at, 0])
                rotate([0, 0, side * 30])
                    cube([spacer_barb, spacer_barb * 3, thickness]);
    }
}

module spacer_label(line, thickness, direction) {
    radius = medal_diameter / 2;
    rotate([0, 0, direction])
        translate([0, radius - 9, medal_thickness - engrave_depth])
            rotate([0, 0, direction == 0 ? 0 : 180])
                linear_extrude(height = engrave_depth * 2)
                    text(line, font = font_name, size = spacer_label_size,
                         halign = "center", valign = "center");
}

module spacer_medal() {
    difference() {
        union() {
            medal_blank();
            spacer_tongue(shimano_thickness, 0);
            spacer_tongue(sram_thickness, 180);
        }
        face_engraving();
        lanyard();
        spacer_label("SHIMANO 1.8", shimano_thickness, 0);
        spacer_label("SRAM 2.8", sram_thickness, 180);
    }
}

// Ключ: шлицевой выступ под внутренние зубцы крышки натяга. Зубцы круглые,
// как у заводского инструмента: угловатые не входят в литые скруглённые пазы
// и срезаются первыми. Печатается стоймя, поэтому обходится без поддержек.
module cap_driver() {
    root = cap_root_diameter;
    tooth = cap_tooth_width / 2;
    translate([0, 0, medal_thickness])
        intersection() {
            union() {
                cylinder(d = root, h = cap_driver_height);
                for (index = [0 : cap_points - 1])
                    rotate([0, 0, index * 360 / cap_points])
                        translate([0, root / 2, 0])
                            cylinder(r = tooth, h = cap_driver_height, $fn = 32);
            }
            // заходный конус: без него ключ приходится ловить вслепую
            cylinder(
                d1 = root + 4 * tooth,
                d2 = root + 2 * tooth - 2 * cap_lead_in,
                h = cap_driver_height
            );
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
                    text(line[index], font = font_name, size = spacer_label_size,
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
