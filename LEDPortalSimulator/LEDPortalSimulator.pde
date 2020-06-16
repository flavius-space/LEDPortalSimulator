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

import processing.video.*;
import java.util.logging.Logger;
import java.awt.GraphicsEnvironment;
import java.awt.GraphicsDevice;
import java.awt.Robot;
import java.awt.image.BufferedImage;
import java.awt.Rectangle;

heronarts.lx.studio.LXStudio lx;

private static final Logger logger = Logger.getLogger(PApplet.class.getName());

LXModel model;
LPSimConfig config;
Movie movie;
Robot robot;
PImage videoFrame;
String[] structures =  {
	"dome_render_6_5_Dome_EDGES",
	"dome_render_6_5_Left_Stack_FACES"
};
//String activeModel = "dome_render_6_5_Test_9_4_LEDs";
// String activeModel = "dome_render_6_5_LEDs_Iso_1220_ALL_PANELS";
// String activeModel = "dome_render_6_5_LEDs_Iso_1220_PANELS_0";
// String activeModel = "dome_render_6_5_LEDs_Iso_1220_Single_ALL_PANELS";
String activeModel = "dome_render_6_5_Dome_ALL_PANELS";
// String activeModel = "dome_render_6_5_Test_12_10_LEDs";
// float[][] screencapBounds;
float[] screencapBounds = new float[]{ 0, 0, 1, 1 };
Rectangle screencapRectangle;

// GraphicsEnvironment activeEnvironment;
GraphicsDevice activeScreen;

String activeMovie;
// String activeMovie = "Steamed Hams.mp4";

PMatrix3D flattener;
PMatrix3D unflattener;
float[][] flatBounds;
float[][] modelBounds;

void setup() {
	// Processing setup, constructs the window and the LX instance
	size(1280, 720, P3D);

	config = new LPSimConfig();
	config.updateFromJSONObject(loadJSONObject(activeModel + ".json"));
	for(String structure : structures) {
		config.updateFromJSONObject(loadJSONObject(structure + ".json"));
	}
	model = modelFromPanels(config.panels);
	flattener = config.getWorldFlattener();
	unflattener = config.getWorldUnflattener();
	modelBounds = config.getModelBounds();
	flatBounds = config.getModelFlatBounds();

	// debugSetup();

	lx = new heronarts.lx.studio.LXStudio(this, model, MULTITHREADED);

	if(videoFrame == null) videoSetup();

	lx.ui.setCoordinateSystem(heronarts.p3lx.ui.UI.CoordinateSystem.valueOf("RIGHT_HANDED"));
	lx.ui.setResizable(RESIZABLE);
}

void debugSetup() {
	List<PVector> modelWorldPoints = new ArrayList<PVector>();

	for(LPPanel panel : config.panels) {
		List<PVector> worldPoints = panel.getWorldVertices();
		PVector centroid = panel.getWorldCentroid();
		modelWorldPoints.add(centroid);
		worldPoints.add(0, centroid);
		PVector normal = panel.getWorldNormal();
		worldPoints.add(PVector.add(centroid, normal));
		LPStructure panelStruct = new LPStructure().updateFromPlaneDebugPoints(worldPoints);
		config.debugStructures.add(panelStruct);

		List<PVector> flattenedWorldPoints = new ArrayList<PVector>();
		for(PVector point: worldPoints) {
			flattenedWorldPoints.add(LPMeshable.coordinateTransform(flattener, point));
		}
		LPStructure flattenedPanelStruct = new LPStructure()
			.updateFromPlaneDebugPoints(flattenedWorldPoints);
		config.debugStructures.add(flattenedPanelStruct);
	}

	PVector modelWorldCentroid = config.getWorldCentroid();
	modelWorldPoints.add(0, modelWorldCentroid);
	PVector modelWorldNormal = config.getWorldNormal();
	modelWorldPoints.add(PVector.add(modelWorldCentroid, modelWorldNormal));

	logger.info(String.format(
		"modelWorldPoints: %s", LPMeshable.formatPVectorList(modelWorldPoints)));

	LPStructure modelStruct = new LPStructure().updateFromPlaneDebugPoints(modelWorldPoints);
	config.debugStructures.add(modelStruct);

	List<PVector> flatModelWorldPoints = new ArrayList<PVector>();
	for(PVector point: modelWorldPoints) {
		flatModelWorldPoints.add(LPMeshable.coordinateTransform(flattener, point));
	}

	LPStructure flattenedModelStruct = new LPStructure()
		.updateFromPlaneDebugPoints(flatModelWorldPoints);
	config.debugStructures.add(flattenedModelStruct);

	logger.info(String.format(
		"flatModelWorldPoints: %s", LPMeshable.formatPVectorList(flatModelWorldPoints)));

	List<PVector> flatBoundsPolygon = new ArrayList<PVector>();
	flatBoundsPolygon.add(new PVector(flatBounds[0][0], flatBounds[1][0], flatBounds[2][0]));
	flatBoundsPolygon.add(new PVector(flatBounds[0][1], flatBounds[1][0], flatBounds[2][0]));
	flatBoundsPolygon.add(new PVector(flatBounds[0][1], flatBounds[1][1], flatBounds[2][0]));
	flatBoundsPolygon.add(new PVector(flatBounds[0][0], flatBounds[1][1], flatBounds[2][0]));
	flatBoundsPolygon.add(new PVector(flatBounds[0][0], flatBounds[1][0], flatBounds[2][1]));
	flatBoundsPolygon.add(new PVector(flatBounds[0][1], flatBounds[1][0], flatBounds[2][1]));
	flatBoundsPolygon.add(new PVector(flatBounds[0][1], flatBounds[1][1], flatBounds[2][1]));
	flatBoundsPolygon.add(new PVector(flatBounds[0][0], flatBounds[1][1], flatBounds[2][1]));

	LPStructure flatBoundsStruct = new LPStructure()
		.updateFromPolygon(flatBoundsPolygon);
	config.debugStructures.add(flatBoundsStruct);

	List<PVector> modelBoundsPolygon = new ArrayList<PVector>();
	modelBoundsPolygon.add(new PVector(modelBounds[0][0], modelBounds[1][0], modelBounds[2][0]));
	modelBoundsPolygon.add(new PVector(modelBounds[0][1], modelBounds[1][0], modelBounds[2][0]));
	modelBoundsPolygon.add(new PVector(modelBounds[0][1], modelBounds[1][1], modelBounds[2][0]));
	modelBoundsPolygon.add(new PVector(modelBounds[0][0], modelBounds[1][1], modelBounds[2][0]));
	modelBoundsPolygon.add(new PVector(modelBounds[0][0], modelBounds[1][0], modelBounds[2][1]));
	modelBoundsPolygon.add(new PVector(modelBounds[0][1], modelBounds[1][0], modelBounds[2][1]));
	modelBoundsPolygon.add(new PVector(modelBounds[0][1], modelBounds[1][1], modelBounds[2][1]));
	modelBoundsPolygon.add(new PVector(modelBounds[0][0], modelBounds[1][1], modelBounds[2][1]));

	LPStructure modelBoundsPolygonStruct = new LPStructure()
		.updateFromPolygon(modelBoundsPolygon);
	config.debugStructures.add(modelBoundsPolygonStruct);

	PMatrix3D identity = new PMatrix3D();
	identity.apply(flattener);
	identity.apply(unflattener);

	logger.info(String.format("identity: %s", LPMeshable.formatPMatrix3D(identity)));
}

void videoSetup() {
	if (activeMovie != null) {
		movie = new Movie((PApplet)this, activeMovie);
		movie.loop();
		while(!movie.available());
		movie.read();
		videoFrame = createImage(movie.width, movie.height, RGB);
	} else if (screencapBounds != null) {
		activeScreen = GraphicsEnvironment.getLocalGraphicsEnvironment().getDefaultScreenDevice();
		int activeScreenWidth = activeScreen.getDisplayMode().getWidth();
		int activeScreenHeight = activeScreen.getDisplayMode().getHeight();
		logger.info(String.format(
			"active screen dimensions: [%d, %d]", activeScreenWidth, activeScreenHeight));
		screencapRectangle = new Rectangle(
			int(screencapBounds[0] * activeScreenWidth),
			int(screencapBounds[1] * activeScreenHeight),
			int(screencapBounds[2] * activeScreenWidth),
			int(screencapBounds[3] * activeScreenHeight)
		);
		logger.info(String.format(
			"screencap rectangle: %s", screencapRectangle));
		try {
			robot = new Robot(activeScreen);
		} catch (Exception e) {
			logger.warning(e.getMessage());
		}
		BufferedImage screenBuffer = robot.createScreenCapture(screencapRectangle);
		videoFrame = new PImage(screenBuffer);
	}
	logger.info(String.format("videoFrame: %d x %d", videoFrame.width, videoFrame.height));
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
		// int pointIndex = 0;
		int pointIndex = 214 * 6;
		int nPoints = 340;
		int nChannels = 8;
		PixelBlazeExpanderOutput output = new PixelBlazeExpanderParentOutput(lx, this, SERIAL_PORT);
		for (int channelNumber = 0; channelNumber < nChannels; channelNumber++) {
			int[] points = new int[nPoints];
			for (int i = 0; i < nPoints; i++) {
				points[i] = pointIndex;
				if (pointIndex < lx.total - 1) pointIndex++;
			}
			PixelBlazeExpanderOutput child = new PixelBlazeExpanderWS281XOutput(lx, this, SERIAL_PORT, channelNumber, points);
			// PixelBlazeExpanderOutput child = new PixelBlazeExpanderAPA102DataOutput(lx, this, SERIAL_PORT, channelNumber, APA102_FREQ, points);
			child.gammaCorrection.setNormalized(0.5);
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

	onUIReadyMovie(lx, ui);

	ui.preview.addComponent(new UIAxes());
}

void onUIReadyMovie(heronarts.lx.studio.LXStudio lx, heronarts.lx.studio.LXStudio.UI ui) {
	if(videoFrame == null) videoSetup();
	List<float[]> vertexUVPairs = new ArrayList<float[]>();

	vertexUVPairs.add(new float[]{flatBounds[0][0], flatBounds[1][0], 0, 0, 0});
	vertexUVPairs.add(new float[]{flatBounds[0][1], flatBounds[1][0], 0, videoFrame.width, 0});
	vertexUVPairs.add(new float[]{flatBounds[0][1], flatBounds[1][1], 0, videoFrame.width, videoFrame.height});
	vertexUVPairs.add(new float[]{flatBounds[0][0], flatBounds[1][1], 0, 0, videoFrame.height});
	for(float[] vertexUVPair : vertexUVPairs) {
		PVector uvPosition = new PVector(vertexUVPair[0], vertexUVPair[1], vertexUVPair[2]);
		PVector unflattened = LPMeshable.coordinateTransform(unflattener, uvPosition);
		vertexUVPair[0] = unflattened.x;
		vertexUVPair[1] = unflattened.y;
		vertexUVPair[2] = unflattened.z;
		logger.fine(String.format(
			"unflattened uv position %s to %s", LPMeshable.formatPVector(uvPosition),
			LPMeshable.formatPVector(unflattened)));
	}
	ui.preview.addComponent(new UIMovie(vertexUVPairs));

}

void draw() {
	if (screencapRectangle != null) {
		PImage screenBuffer = new PImage(robot.createScreenCapture(screencapRectangle));
		videoFrame.copy(
			screenBuffer,
			0,
			0,
			screenBuffer.width,
			screenBuffer.height,
			0,
			0,
			screenBuffer.width,
			screenBuffer.height
		);
	}
}

void movieEvent(Movie m) {
	m.read();
	if(videoFrame != null) videoFrame.copy(m, 0, 0, m.width, m.height, 0, 0, m.width, m.height);
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
