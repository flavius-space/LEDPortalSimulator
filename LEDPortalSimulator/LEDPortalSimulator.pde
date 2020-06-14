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

import java.util.logging.Logger;
heronarts.lx.studio.LXStudio lx;

private static final Logger logger = Logger.getLogger(PApplet.class.getName());
LXModel model;
LPSimConfig config;
String[] structures =  {
	"dome_render_6_5_Dome_EDGES",
	"dome_render_6_5_Left_Stack_FACES"
};
String activeModel = "dome_render_6_5_LEDs_Iso_1220_ALL_PANELS";
// String activeModel = "dome_render_6_5_LEDs_Iso_1220_PANELS_0";
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

	int vertexIndex;

	List<PVector> panelWorldCentroids = new ArrayList<PVector>();
	List<PVector> panelWorldNormals = new ArrayList<PVector>();
	for(LPPanel panel : config.panels) {
		LPStructure panelStruct = new LPStructure();
		List<PVector> worldVertices = panel.getWorldVertices();
		PVector worldCentroid = LPMeshable.getCentroid(worldVertices);
		panelWorldCentroids.add(worldCentroid);
		panelStruct.vertices.add(worldCentroid);
		vertexIndex = 1;
		for(PVector vertex: worldVertices) {
			panelStruct.vertices.add(vertex);
			panelStruct.edges.add(new int[]{0, vertexIndex});
			vertexIndex += 1;
		}
		PVector worldNormal = LPMeshable.getNormal(worldVertices);
		panelWorldNormals.add(worldNormal);
		panelStruct.vertices.add(PVector.add(worldCentroid, worldNormal));
		panelStruct.edges.add(new int[]{0, vertexIndex});
		config.debugStructures.add(panelStruct);
	}

	vertexIndex = 1;
	LPStructure modelStruct = new LPStructure();
	PVector modelWorldCentroid = LPMeshable.getCentroid(panelWorldCentroids);
	modelStruct.vertices.add(modelWorldCentroid);
	for(PVector panelWorldCentroid: panelWorldCentroids) {
		modelStruct.vertices.add(panelWorldCentroid);
		modelStruct.edges.add(new int[]{0, vertexIndex});
		vertexIndex += 1;
	}
	PVector modelWorldNormal = LPMeshable.getCentroid(panelWorldCentroids);
	modelStruct.vertices.add(PVector.add(modelWorldCentroid, modelWorldNormal));
	modelStruct.edges.add(new int[]{0, vertexIndex});
	config.debugStructures.add(modelStruct);


	lx = new heronarts.lx.studio.LXStudio(this, model, MULTITHREADED);
	// lx.ui.setCoordinateSystem(heronarts.p3lx.ui.UI.CoordinateSystem.valueOf("LEFT_HANDED"));
	lx.ui.setCoordinateSystem(heronarts.p3lx.ui.UI.CoordinateSystem.valueOf("RIGHT_HANDED"));
	lx.ui.setResizable(RESIZABLE);
}


// final String OPC_IP = "192.168.1.20";
// final String OPC_IP = "127.0.0.1";
// final int OPC_PORT = 42069;
// final byte OPC_CHANNEL = 0;
final String SERIAL_PORT = "/dev/tty.usbserial-AD025M69";
// final int APA102_CLOCK_CHANNEL = 7;
// final int APA102_FREQ = 800000;

void initialize(final heronarts.lx.studio.LXStudio lx, heronarts.lx.studio.LXStudio.UI ui) {
	// Add custom components or output drivers here
	try {
		int pointIndex = 0;
		int nPoints = 300;
		int nChannels = 1;
		PixelBlazeExpanderOutput output = new PixelBlazeExpanderParentOutput(lx, this, SERIAL_PORT);
		for (int channelNumber = 0; channelNumber < nChannels; channelNumber++) {
			int[] points = new int[nPoints];
			for (int i = 0; i < nPoints; i++) {
				points[i] = pointIndex;
				if (pointIndex < lx.total - 1) pointIndex++;
			}
			PixelBlazeExpanderOutput child = new PixelBlazeExpanderWS281XOutput(lx, this, SERIAL_PORT, channelNumber, points);
			// PixelBlazeExpanderOutput child = new PixelBlazeExpanderAPA102DataOutput(lx, this, SERIAL_PORT, channelNumber, APA102_FREQ, points);
			output.addChild(child);
		}
		// PixelBlazeExpanderOutput clock = new PixelBlazeExpanderAPA102ClockOutput(lx, this, SERIAL_PORT, APA102_CLOCK_CHANNEL, APA102_FREQ);
		// output.addChild(clock);
		PixelBlazeExpanderOutput sendAll = new PixelBlazeExpanderSendAllOutput(lx, this, SERIAL_PORT);
		output.addChild(sendAll);
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
	for(LPStructure debugStructure: config.debugStructures) {
		ui.preview.addComponent(new UIDebugWireFrame(debugStructure));
	}

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
