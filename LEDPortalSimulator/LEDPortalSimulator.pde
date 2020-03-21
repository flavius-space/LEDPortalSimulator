/**
 * By using LX Studio, you agree to the terms of the LX Studio Software
 * License and Distribution Agreement, available at: http://lx.studio/license
 *
 * Please note that the LX license is not open-source. The license
 * allows for free, non-commercial use.
 *
 * HERON ARTS MAKES NO WARRANTY, EXPRESS, IMPLIED, STATUTORY, OR
 * OTHERWISE, AND SPECIFICALLY DISCLAIMS ANY WARRANTY OF
 * MERCHANTABILITY, NON-INFRINGEMENT, OR FITNESS FOR A PARTICULAR
 * PURPOSE, WITH RESPECT TO THE SOFTWARE.
 */

heronarts.lx.studio.LXStudio lx;
// UISkeleton skele;
LXModel model;
LPSimConfig LPSimConfig;
String activeModel = "dome_render_6_5_LEDs_Compromise";

void setup() {
	// Processing setup, constructs the window and the LX instance
	size(1280, 720, P3D);

	LPSimConfig = LPSimConfig.fromJSONObject(loadJSONObject(activeModel + ".json"));
    model = modelFromPanels(LPSimConfig.panels);

	// skele = new UISkeleton(LPSimConfig.skeleConfig);

	lx = new heronarts.lx.studio.LXStudio(this, model, MULTITHREADED);
	lx.ui.setResizable(RESIZABLE);
}

void initialize(final heronarts.lx.studio.LXStudio lx, heronarts.lx.studio.LXStudio.UI ui) {
	// Add custom components or output drivers here
}

void onUIReady(heronarts.lx.studio.LXStudio lx, heronarts.lx.studio.LXStudio.UI ui) {
	// Add custom UI components here
	// ui.preview.addComponent(skele);
}

void draw() {
}

// Configuration flags
final static boolean MULTITHREADED = true;
final static boolean RESIZABLE = true;

// Helpful global constants
final static float INCHES = 1;
final static float IN = INCHES;
final static float FEET = 12 * INCHES;
final static float FT = FEET;
final static float CM = IN / 2.54;
final static float MM = CM * .1;
final static float M_ = CM * 100;
final static float METER = M_;
final static float METRE = M_;
