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
LPSimConfig config;
String[] structures =  {
	"dome_render_6_5_Dome_EDGES",
	"dome_render_6_5_Left_Stack_FACES"
};
String activeModel = "dome_render_6_5_LEDs_Compromise_LEDs";
// String activeModel = "dome_render_6_5_Test_12_10_LEDs";

void setup() {
	// Processing setup, constructs the window and the LX instance
	size(1280, 720, P3D);

	config = new LPSimConfig();
	config.updateFromJSONObject(loadJSONObject(activeModel + ".json"));
	for(String structure : structures) {
		config.updateFromJSONObject(loadJSONObject(structure + ".json"));
	}
	model = modelFromPanels(config.panels);

	lx = new heronarts.lx.studio.LXStudio(this, model, MULTITHREADED);
	// lx.ui.setCoordinateSystem(heronarts.p3lx.ui.UI.CoordinateSystem.valueOf("LEFT_HANDED"));
	lx.ui.setCoordinateSystem(heronarts.p3lx.ui.UI.CoordinateSystem.valueOf("RIGHT_HANDED"));
	lx.ui.setResizable(RESIZABLE);
}

final String OPC_IP = "192.168.1.20";
// final String OPC_IP = "127.0.0.1";
final int OPC_PORT = 42069;
final byte OPC_CHANNEL = 0;
final String SERIAL_PORT = "/dev/tty.usbserial-AD025M69";

void initialize(final heronarts.lx.studio.LXStudio lx, heronarts.lx.studio.LXStudio.UI ui) {
	// Add custom components or output drivers here
	try {
		int[] firstNPoints = new int[1];
		for (int i = 0; i < firstNPoints.length; ++i) {
			firstNPoints[i] = i;
		}

		PixelBlazeExpanderOutput output = new PixelBlazeExpanderOutput(lx, this, SERIAL_PORT, firstNPoints);

		// TCP:

		// First N Points
		// OPCOutput output =
		// 	new OPCOutput(lx, OPC_IP, OPC_PORT, firstNPoints);
		// All points
			// new OPCOutput(lx, OPC_IP, OPC_PORT, lx.model);

		// output.setChannel(OPC_CHANNEL);

		// UDP:

		// LXDatagramOutput output = new LXDatagramOutput(lx);

		// UDP: First N Points
		// OPCDatagram datagram
		// 	 = new OPCDatagram(firstNPoints);
		// UDP: All points
			//  = new OPCDatagram(lx.model);

		// datagram.setAddress(OPC_IP);
		// datagram.setPort(OPC_PORT);
		// datagram.setChannel(OPC_CHANNEL);
		// output.addDatagram(datagram);

		// Add the output to the LX engine
		lx.addOutput(output);
	} catch (Exception x) {
		x.printStackTrace();
	}
}

void onUIReady(heronarts.lx.studio.LXStudio lx, heronarts.lx.studio.LXStudio.UI ui) {
	// Add custom UI components here
	for(LPStructure structure: config.structures) {
		ui.preview.addComponent(new UIWireframe(structure));
	}
	// ui.preview.addComponent(new UIAxes());
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
