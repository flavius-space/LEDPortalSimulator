import java.util.logging.Logger;

// Note: For some reason it's easier to render with Y ans Z swapped
public class UIWireframe extends UI3dComponent {
	public int colour = #ffffff;
	public float alpha = 100;
	LPStructure data;
	List<PVector[]> edges;
	public UIWireframe(LPStructure data, int colour) {
		this.data = data;
		this.edges = data.getWorldEdges();
		this.colour = colour;
	}
	public UIWireframe(LPStructure data) {
		this(data, #ffffff);
	}
    @Override
    protected void onDraw(UI ui, PGraphics pg){
		pg.pushStyle();
		pg.strokeWeight(5);
		pg.stroke(this.colour, alpha);
		for (PVector[] edge: this.edges) {
			PVector start = LPMeshable.worldUITransform(edge[0]);
			PVector end = LPMeshable.worldUITransform(edge[1]);
			pg.line(start.x, start.y, start.z, end.x, end.y, end.z);
		}
		pg.popStyle();
	}
}

public class UIDebugWireFrame extends UIWireframe {
	// private static final Logger logger = Logger.getLogger(UIDebugWireFrame.class.getName());
	public UIDebugWireFrame(LPStructure data) {
		super(data, #ff0000);
		// logger.info(String.format(
		// 	"vertices: %s, edges: %s", LPMeshable.formatPVectorList(data.vertices)
		// ));
	}
}

public class UIAxes extends UI3dComponent {
	public UIAxes() {
		super();
		this.addChild(new BillboardText("X", LPMeshable.xAxis, 1, #ff0000));
		this.addChild(new BillboardText("Y", LPMeshable.yAxis, 1, #00ff00));
		this.addChild(new BillboardText("Z", LPMeshable.zAxis, 1, #0000ff));
	}
    @Override
    protected void onDraw(UI ui, PGraphics pg){
		pg.pushStyle();
		// pg.strokeWeight(5);

		PVector uiX = LPMeshable.worldUITransform(LPMeshable.xAxis);
		PVector uiY = LPMeshable.worldUITransform(LPMeshable.yAxis);
		PVector uiZ = LPMeshable.worldUITransform(LPMeshable.zAxis);
		pg.stroke(#ff0000);
		pg.line(0, 0, 0, uiX.x, uiX.y, uiX.z);
		pg.stroke(#00ff00);
		pg.line(0, 0, 0, uiY.x, uiY.y, uiY.z);
		pg.stroke(#0000ff);
		pg.line(0, 0, 0, uiZ.x, uiZ.y, uiZ.z);
		pg.popStyle();
	}
}

public class BillboardText extends UI3dComponent {
	public String text;
	public PVector position;
	public float s;
	public color c;
	public BillboardText(String text, PVector position, float s, color c) {
		super();
		this.text = text;
		this.position = position;
		this.s = s;
		this.c = c;
	}
    @Override
    void onDraw(UI ui, PGraphics pg){
		PVector uiPosition = LPMeshable.worldUITransform(this.position);
		pg.pushStyle();
		pg.textMode(SHAPE);
		pg.fill(this.c);
		pg.textSize(this.s);
		pg.text(this.text, uiPosition.x, uiPosition.y, uiPosition.z);
		pg.popStyle();
	}
}

public class UIMovie extends UI3dComponent {
	public List<float[]> vertexUVPairs;
	public UIMovie(List<float[]> vertexUVPairs) {
		this.vertexUVPairs = vertexUVPairs;
	}

    @Override
    void onDraw(UI ui, PGraphics pg){
		pg.pushStyle();
		pg.noStroke();
		pg.beginShape();
		pg.texture(movieFrame);
		int i = 0;

		for(float[] vertexUVPair : this.vertexUVPairs) {
			PVector uiPosition = LPMeshable.worldUITransform(new PVector(
				vertexUVPair[0], vertexUVPair[1], vertexUVPair[2]));
			pg.vertex(uiPosition.x, uiPosition.y, uiPosition.z, vertexUVPair[3], vertexUVPair[4]);
		}
		pg.endShape();
		pg.popStyle();
	}
}
