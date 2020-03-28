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
// String activeModel = "dome_render_6_5_LEDs_Compromise_LEDs";
String activeModel = "dome_render_6_5_Test_12_10_LEDs";

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

	final String OPC_PI = "192.168.1.20";
	final int OPC_PORT = 42069;
	final byte OPC_CHANNEL = 0;

void initialize(final heronarts.lx.studio.LXStudio lx, heronarts.lx.studio.LXStudio.UI ui) {
	// Add custom components or output drivers here
	try {
		// This does all outputs (too many)
		// OPCOutput output = new OPCOutput(lx, OPC_PI, OPC_PORT, lx.model);
		// output.setChannel(OPC_CHANNEL);

		// Construct a new DatagramOutput object
		// LXDatagramOutput output = new LXDatagramOutput(lx);

		// Add an OPCDatagram which sends all of the points in our model
		// OPCDatagram datagram = new OPCDatagram(lx.model);
		// datagram.setAddress(OPC_PI);
		// datagram.setPort(OPC_PORT);
		// datagram.setChannel((byte)4);
		// output.addDatagram(datagram);

		// Here's an example of a custom OPCDatagram which only sends specific points
		// int universeNumber = 0;
		// int[] first100Points = new int[100];
		// for (int i = 0; i < first100Points.length; ++i) {
		// 	first100Points[i] = i;
		// }
		// OPCDatagram first100PointsDatagram = new OPCDatagram(first100Points, universeNumber);
		// first100PointsDatagram.setAddress(ARTNET_IP);
		// output.addDatagram(datagram);

		int[] first120Points = new int[120];
		for (int i = 0; i < first120Points.length; ++i) {
			first120Points[i] = i;
		}

		OPCOutput output = new OPCOutput(lx, OPC_PI, OPC_PORT, first120Points);
		output.setChannel(OPC_CHANNEL);

		// Add the datagram output to the LX engine
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
