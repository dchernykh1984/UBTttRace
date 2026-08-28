// Кубок победителя UBT TT — разделочный велосипед на подставке.
//
// Печатается двумя деталями:
//   base — подставка с гравировкой (текст спереди, логотип по бокам);
//   bike — силуэт велосипеда, лежит плашмя, поэтому печатается без поддержек
//          и не расслаивается.
// Велосипед садится в пазы подставки. part = "all" собирает их для предпросмотра.
//
//   openscad -o bike.stl -D 'part="bike"' trophy.scad

/* [Что печатать] */
part = "all"; // [all, base, bike]

/* [Надписи на подставке] */
title_line = "UBT TT · 04.10.2026";
place_line = "Победитель · Жеңімпаз";
category_line = "Мужчины · Ерлер";
font_name = "DejaVu Sans:style=Bold";
logo_file = "ubt-logo.svg";
giant_file = "giant-logo.svg";
// Ширина обоих контуров в файлах — 100 единиц, высота у каждого своя.
logo_source_height = 129.4;
giant_source_width = 99.81;

text_size = 4.0;
text_depth = 0.8;
text_step = 6.5;
logo_height = 28;
wheel_logo_height = 46;
giant_base_length = 62;
giant_tube_length = 26;
logo_depth = 0.8;

/* [Подставка] */
base_length = 132;
base_depth = 50;
base_height = 36;
base_corner = 8;
base_taper = 3;

/* [Велосипед] */
wheel_diameter = 62;
wheelbase = 93;
frame_thickness = 8;
down_tube_width = 7.5;
down_tube_top_width = 6;
wheel_overlap = 2;
// Насколько рама заходит на колесо — так перья с ним срастаются.

/* [Тортик] */
// Гонка приурочена ко дню рождения команды, поэтому рядом с велосипедом
// стоит тортик со свечкой — такой же плоской фигурой, только в своей плоскости.
cake_width = 28;
cake_base_height = 12;
cake_top_width = 19;
cake_top_height = 7;
cake_drops = 4;
cake_drop = 2;
candle_width = 3;
candle_height = 10;
flame_width = 5;
flame_height = 7.5;
// Единственное место, где тортик виден целиком: просвет между колёсами.
// Правее его закрывает переднее колесо, левее — заднее.
cake_x = 7;
bike_offset_y = 13;
cake_offset_y = -13;

/* [Соединение] */
foot_width = 14;
foot_depth = 15;
socket_clearance = 0.35;

// Гранёность держим умеренной: CGAL в OpenSCAD считает объединение
// тысяч треугольников очень долго, а на печати разница не видна.
$fn = 48;

R = wheel_diameter / 2;
rear_axle = [0, R];
front_axle = [wheelbase, R];
bottom_bracket = [40, 24];
seat_top = [26, 80];
head_top = [80, 70];
head_bottom = [85, 55];
// Нижняя труба приходит к рулевой высоко, почти под верхнюю: иначе она
// врезалась бы в переднее колесо.
down_tube_top = [82, 63];
foot_sink = 9;

module tube(p1, p2, w1, w2) {
    hull() {
        translate(p1) circle(d = w1);
        translate(p2) circle(d = w2);
    }
}

module rear_disc() {
    translate(rear_axle) circle(r = R);
}

// Переднее колесо — трёхлистник: спицы сделали бы модель хрупкой,
// а на разделочном велосипеде такое колесо и стоит.
module trispoke() {
    rim = 8;
    translate(front_axle) {
        difference() { circle(r = R); circle(r = R - rim); }
        circle(r = 5.5);
        for (angle = [90, 210, 330])
            rotate(angle) polygon([[-4, 3], [4, 3], [6.5, R - rim + 1], [-6.5, R - rim + 1]]);
    }
}

// Подседельная труба и верхние перья облегают заднее колесо — это главная
// примета разделочной рамы. Лишнее срезаем самим колесом с зазором.
module aero_rear_triangle() {
    difference() {
        union() {
            tube(bottom_bracket, seat_top, 11, 9);
            tube(rear_axle + [4, 0], seat_top, 7, 9);
        }
        translate(rear_axle) circle(r = R - wheel_overlap);
    }
}

module frame() {
    aero_rear_triangle();
    tube(bottom_bracket, rear_axle, 5.5, 3.5);   // нижние перья
    tube(bottom_bracket, down_tube_top, down_tube_width, down_tube_top_width);
    tube(seat_top, head_top, 6, 5);              // верхняя труба
    tube(head_top, head_bottom, 6.5, 6.5);       // рулевая
    tube(head_bottom, front_axle, 6, 3.5);       // вилка

    tube(seat_top, [26, 82], 6, 5);              // мачта подседельного штыря
    tube([19, 83], [38, 84], 3.5, 3);            // седло

    tube(head_top, [106, 79], 5, 3.5);           // лежак
    tube([106, 79], [110, 88], 3.5, 3);          // рог лежака
    tube([84, 79], [97, 79], 4, 4);              // подлокотник

    difference() {
        union() {
            translate(bottom_bracket) circle(r = 8);
            // Шатун смотрит вниз и чуть вперёд. Педали нет: сбоку от каретки
            // она была бы тонкой и хрупкой, а в профиль сливалась бы с рамой.
            tube(bottom_bracket, bottom_bracket + [5, -11], 4.5, 3.5);
        }
        translate(rear_axle) circle(r = R - wheel_overlap);
    }
}

module feet() {
    for (x = [rear_axle[0], front_axle[0]])
        translate([x - foot_width / 2, -foot_sink]) square([foot_width, foot_depth]);
}

module bike() {
    difference() {
        linear_extrude(height = frame_thickness) {
            frame();
            feet();
            rear_disc();
            trispoke();
        }
        wheel_logos();
        down_tube_logos();
    }
}

// Логотип партнёра лежит вдоль нижней трубы — там же, где на настоящей раме.
// Зеркалим сам контур до поворота, иначе на обратной стороне он ляжет
// поперёк трубы.
module down_tube_logos() {
    middle = (bottom_bracket + down_tube_top) / 2;
    angle = atan2(
        down_tube_top[1] - bottom_bracket[1],
        down_tube_top[0] - bottom_bracket[0]
    );
    for (side = [0, 1])
        translate([middle[0], middle[1], side * frame_thickness])
            rotate([0, 0, angle])
                mirror([1 - side, 0, 0])
                    giant_plate(giant_tube_length);
}

// Дисковое колесо — самое видное место кубка, логотип идёт на обе его стороны.
// Дальнюю сторону зеркалим, иначе с той стороны надпись читалась бы наоборот.
module wheel_logos() {
    for (side = [0, 1])
        translate([rear_axle[0], rear_axle[1], side * frame_thickness])
            mirror([1 - side, 0, 0])
                linear_extrude(height = logo_depth * 2, center = true)
                    scale(wheel_logo_height / logo_source_height)
                        import(logo_file, center = true);
}

module cake_tier(width, height, y) {
    half = width / 2;
    translate([0, y])
        hull() {
            for (side = [-1, 1]) {
                translate([side * (half - 2), 2]) circle(r = 2);
                translate([side * (half - 2), height - 2]) circle(r = 2);
            }
        }
}

module cake_profile() {
    top = cake_base_height + cake_top_height;
    cake_tier(cake_width, cake_base_height, 0);
    cake_tier(cake_top_width, cake_top_height, cake_base_height);

    // Капли крема по краю верхнего яруса; их чётное число, чтобы середина
    // осталась свободной под свечку.
    step = (cake_top_width - cake_drop) / cake_drops;
    for (index = [0 : cake_drops - 1])
        translate([-(cake_top_width - cake_drop - step) / 2 + index * step, top])
            circle(r = cake_drop);

    translate([-candle_width / 2, top]) square([candle_width, candle_height]);
    hull() {
        translate([0, top + candle_height + flame_width / 2]) circle(d = flame_width);
        translate([0, top + candle_height + flame_height]) circle(d = 0.8);
    }
}

module cake_foot() {
    translate([-foot_width / 2, -foot_sink]) square([foot_width, foot_sink + 4]);
}

module cake() {
    linear_extrude(height = frame_thickness) {
        cake_profile();
        cake_foot();
    }
}

module rounded_plinth() {
    offset_x = base_length / 2 - base_corner;
    offset_y = base_depth / 2 - base_corner;
    hull() {
        for (x = [-offset_x, offset_x], y = [-offset_y, offset_y])
            translate([x, y, 0]) cylinder(r = base_corner, h = base_height - base_taper);
        for (x = [-offset_x + base_taper, offset_x - base_taper],
             y = [-offset_y + base_taper, offset_y - base_taper])
            translate([x, y, 0]) cylinder(r = base_corner, h = base_height);
    }
}

module engraved_text() {
    lines = [title_line, place_line, category_line];
    first = (len(lines) - 1) / 2;
    for (index = [0 : len(lines) - 1])
        translate([0, -base_depth / 2, base_height / 2 + (first - index) * text_step])
            rotate([90, 0, 0])
                linear_extrude(height = text_depth * 2, center = true)
                    text(lines[index], font = font_name, size = text_size,
                         halign = "center", valign = "center");
}

module logo_plate() {
    linear_extrude(height = logo_depth * 2, center = true)
        scale(logo_height / logo_source_height)
            import(logo_file, center = true);
}

module giant_plate(length) {
    linear_extrude(height = logo_depth * 2, center = true)
        scale(length / giant_source_width)
            import(giant_file, center = true);
}

// Лицевая грань занята текстом, логотип команды идёт на боковые,
// а на задней — логотип партнёра гонки.
module engraved_logos() {
    z = base_height / 2;
    translate([-base_length / 2, 0, z]) rotate([90, 0, -90]) logo_plate();
    translate([base_length / 2, 0, z]) rotate([90, 0, 90]) logo_plate();
    translate([0, base_depth / 2, z]) rotate([90, 0, 180]) giant_plate(giant_base_length);
}

function bike_span() = [-foot_width / 2, 110];
function bike_shift() = -(bike_span()[0] + bike_span()[1]) / 2;

module socket_at(x, y) {
    translate([
        x - (foot_width + socket_clearance) / 2,
        y - (frame_thickness + socket_clearance) / 2,
        base_height - foot_sink,
    ])
        cube([foot_width + socket_clearance, frame_thickness + socket_clearance, foot_sink + 1]);
}

module bike_sockets() {
    for (x = [rear_axle[0], front_axle[0]])
        socket_at(x + bike_shift(), bike_offset_y);
    socket_at(cake_x, cake_offset_y);
}

module base() {
    difference() {
        rounded_plinth();
        engraved_text();
        engraved_logos();
        bike_sockets();
    }
}

module standing_bike() {
    translate([bike_shift(), bike_offset_y + frame_thickness / 2, base_height])
        rotate([90, 0, 0])
            bike();
}

module standing_cake() {
    translate([cake_x, cake_offset_y + frame_thickness / 2, base_height])
        rotate([90, 0, 0])
            cake();
}

if (part == "base") base();
else if (part == "bike") bike();
else if (part == "cake") cake();
else { base(); standing_bike(); standing_cake(); }
