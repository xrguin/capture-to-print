// Plant Label Stake — parametric with customizable text
// For MakerWorld Parametric Model Maker (Customizer)
// Print flat on bed, no supports needed

/* [Label Head] */
// Head width in mm
head_width = 48; // [30:2:80]
// Head height in mm
head_height = 30; // [20:2:50]
// Thickness in mm
thickness = 2; // [1.5:0.5:4]
// Top corner chamfer in mm (angular look)
chamfer_size = 10; // [0:1:20]

/* [Stake] */
// Stake width in mm
stake_width = 10; // [6:1:20]
// Stake length in mm (below head)
stake_length = 55; // [30:5:80]
// Tip taper length in mm
stake_tip_length = 15; // [8:1:25]

/* [Text] */
// Plant name to display
label_text = "Basil";
// Text size in mm
text_size = 8; // [4:1:15]
// Text depth in mm (how much it protrudes or is cut)
text_depth = 0.6; // [0.3:0.1:1.5]
// Text style
text_style = "embossed"; // [embossed:Raised text, engraved:Cut into surface]
// Font
font = "Work Sans"; // [Work Sans, Inter, Montserrat, Noto Sans, Nunito, Open Sans, Oswald, Playfair Display, Raleway, Roboto, Roboto Condensed, Roboto Mono, Roboto Slab, Rubik, Source Sans 3, Ubuntu Sans, Lora, Merriweather Sans, Roboto Serif]
// Font style
font_style = "Bold"; // [Regular, Bold, Italic, Bold Italic, Light, Medium, SemiBold, ExtraBold, Thin, Black]

/* [Hidden] */
$fn = 24;
total_height = head_height + stake_length + stake_tip_length;
label_font = str(font, ":style=", font_style);

// Head center Y position (head sits at top)
head_center_y = stake_length + stake_tip_length + head_height / 2;

// === MODULES ===

module chamfered_rect(w, h, t, c) {
    // Rectangle with chamfered top and bottom corners
    if (c > 0) {
        difference() {
            cube([w, h, t], center = true);
            // Chamfer top-left
            translate([-(w/2), h/2, 0])
                rotate([0, 0, 45])
                    cube([c * 1.42, c * 1.42, t + 1], center = true);
            // Chamfer top-right
            translate([w/2, h/2, 0])
                rotate([0, 0, 45])
                    cube([c * 1.42, c * 1.42, t + 1], center = true);
            // Chamfer bottom-left
            translate([-(w/2), -h/2, 0])
                rotate([0, 0, 45])
                    cube([c * 1.42, c * 1.42, t + 1], center = true);
            // Chamfer bottom-right
            translate([w/2, -h/2, 0])
                rotate([0, 0, 45])
                    cube([c * 1.42, c * 1.42, t + 1], center = true);
        }
    } else {
        cube([w, h, t], center = true);
    }
}

// === MAIN ===

// Combine label body + text
if (text_style == "embossed") {
    // Body
    label_body();
    // Raised text on front face
    translate([0, head_center_y, thickness / 2])
        linear_extrude(text_depth)
            text(label_text, size = text_size, font = label_font,
                 halign = "center", valign = "center");
} else {
    difference() {
        // Body
        label_body();
        // Engraved text into front face
        translate([0, head_center_y, thickness / 2 - text_depth + 0.01])
            linear_extrude(text_depth + 0.1)
                text(label_text, size = text_size, font = label_font,
                     halign = "center", valign = "center");
    }
}

module label_body() {
    // Head — chamfered rectangle
    translate([0, head_center_y, 0])
        chamfered_rect(head_width, head_height, thickness, chamfer_size);

    // Stake — straight section
    stake_center_y = stake_tip_length + stake_length / 2;
    translate([0, stake_center_y, 0])
        cube([stake_width, stake_length, thickness], center = true);

    // Tip — taper to point
    hull() {
        // Top of tip = bottom of stake
        translate([0, stake_tip_length, 0])
            cube([stake_width, 0.1, thickness], center = true);
        // Bottom point
        translate([0, 0, 0])
            cube([1.5, 0.1, thickness * 0.4], center = true);
    }
}

echo(str("Total height: ", total_height, "mm"));
echo(str("Text: \"", label_text, "\" in ", font, " ", font_style));
