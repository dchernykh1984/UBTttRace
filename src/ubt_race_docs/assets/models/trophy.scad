// Кубок победителя UBT TT — параметрическая модель для 3D-печати.
//
// Печатается двумя деталями: подставка со стойкой и чаша. Они соединяются
// штырём — так на столе нет нависаний, кроме ручек чаши, и обе детали влезают
// на небольшой стол. part = "all" собирает их вместе для предпросмотра.
//
// Все надписи и размеры задаются снаружи:
//   openscad -o trophy.stl -D 'part="base"' -D 'category_line="Мужчины · Ерлер"' models/trophy.scad

/* [Что печатать] */
// all — собранный кубок, base — подставка со стойкой, cup — чаша
part = "all"; // [all, base, cup]

/* [Надписи на подставке] */
title_line = "UBT TT · 04.10.2026";
place_line = "1 место · 1-орын";
category_line = "Мужчины · Ерлер";
font_name = "DejaVu Sans:style=Bold";
text_size = 4.4;
text_depth = 0.8;
text_step = 6.5;

/* [Подставка] */
base_width = 86;
base_height = 26;
base_corner = 9;
base_taper = 4;

/* [Стойка] */
stem_height = 42;
stem_bottom_radius = 16;
stem_top_radius = 11;

/* [Чаша] */
cup_height = 56;
cup_bottom_radius = 12;
cup_top_radius = 36;
cup_wall = 4;
cup_rim = 4;
cup_floor = 14;
handle_major_radius = 10;
handle_minor_radius = 3.4;
handle_height_fraction = 0.55;

/* [Соединение] */
peg_radius = 7;
peg_height = 10;
peg_clearance = 0.3;

// Гранёность держим умеренной: CGAL в OpenSCAD считает объединение
// тысяч треугольников очень долго, а на печати разница не видна.
$fn = 48;
handle_fn = 24;

module rounded_plinth(width, height, corner, taper) {
    offset = width / 2 - corner;
    hull() {
        for (x = [-offset, offset], y = [-offset, offset])
            translate([x, y, 0]) cylinder(r = corner, h = height - taper);
        for (x = [-offset + taper, offset - taper], y = [-offset + taper, offset - taper])
            translate([x, y, 0]) cylinder(r = corner, h = height);
    }
}

module engraved_lines() {
    lines = [title_line, place_line, category_line];
    first = (len(lines) - 1) / 2;
    for (index = [0 : len(lines) - 1])
        translate([0, -base_width / 2, base_height / 2 + (first - index) * text_step])
            rotate([90, 0, 0])
                linear_extrude(height = text_depth * 2, center = true)
                    text(
                        lines[index],
                        font = font_name,
                        size = text_size,
                        halign = "center",
                        valign = "center"
                    );
}

module stem() {
    cylinder(r1 = stem_bottom_radius, r2 = stem_top_radius, h = stem_height);
}

// Внешняя форма чаши, ещё без полости.
module cup_shell() {
    rotate_extrude()
        polygon(points = [
            [0, 0],
            [cup_bottom_radius, 0],
            [cup_top_radius, cup_height - cup_rim],
            [cup_top_radius, cup_height],
            [0, cup_height],
        ]);
}

// Полость чаши. Вычитается уже после того, как приделаны ручки, — иначе
// внутренняя половина каждого кольца остаётся торчать внутри чаши.
module cup_cavity() {
    inner_top = cup_top_radius - cup_wall;
    inner_bottom = cup_bottom_radius - cup_wall + 1;
    translate([0, 0, cup_floor])
        rotate_extrude()
            polygon(points = [
                [0, 0],
                [inner_bottom, 0],
                [inner_top, cup_height - cup_floor],
                [0, cup_height - cup_floor],
            ]);
}

module handle() {
    rotate([90, 0, 0])
        rotate_extrude($fn = handle_fn * 2)
            translate([handle_major_radius, 0])
                circle(r = handle_minor_radius, $fn = handle_fn);
}

module handles() {
    z = cup_height * handle_height_fraction;
    radius_at_z =
        cup_bottom_radius + (cup_top_radius - cup_bottom_radius) * z / (cup_height - cup_rim);
    for (side = [-1, 1])
        translate([side * radius_at_z, 0, z]) handle();
}

module cup() {
    difference() {
        union() {
            cup_shell();
            handles();
        }
        cup_cavity();
    }
}

module base() {
    difference() {
        union() {
            rounded_plinth(base_width, base_height, base_corner, base_taper);
            translate([0, 0, base_height]) stem();
            translate([0, 0, base_height + stem_height])
                cylinder(r = peg_radius, h = peg_height);
        }
        engraved_lines();
    }
}

// Гнездо под штырь подставки. Оно сверлится в дне чаши, поэтому дно должно
// быть заметно толще штыря — иначе в чаше появится сквозная дыра.
socket_depth = peg_height + peg_clearance;
assert(
    cup_floor >= socket_depth + 3,
    "дно чаши тоньше гнезда под штырь: увеличьте cup_floor или укоротите peg_height"
);

module cup_with_socket() {
    difference() {
        cup();
        translate([0, 0, -0.01])
            cylinder(r = peg_radius + peg_clearance, h = socket_depth);
    }
}

module assembly() {
    base();
    translate([0, 0, base_height + stem_height]) cup_with_socket();
}

if (part == "base") base();
else if (part == "cup") cup_with_socket();
else assembly();
