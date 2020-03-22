// Note: For some reason it's easier to render with Y ans Z swapped

public class UIWireframe extends UI3dComponent {
	public int colour = #ffffff;
	public float alpha = 100;
	LPStructure data;
	List<PVector[]> edges;
	public UIWireframe(LPStructure data) {
		this.data = data;
		this.edges = data.getWorldEdges();
	}
    @Override
    protected void onDraw(UI ui, PGraphics pg){
		pg.pushStyle();
		pg.strokeWeight(5);
		pg.stroke(this.colour, alpha);
		for (PVector[] edge: this.edges) {
			PVector start = edge[0];
			PVector end = edge[1];
			pg.line(start.x, start.y, start.z, end.x, end.y, end.z);
		}
		pg.popStyle();
	}
}

public class UIAxes extends UI3dComponent {
	public UIAxes() {
		super();
		this.addChild(new BillboardText("X", 1, 0, 0, 1, #ff0000));
		this.addChild(new BillboardText("Y", 0, 1, 0, 1, #00ff00));
		this.addChild(new BillboardText("Z", 0, 0, 1, 1, #0000ff));
	}
    @Override
    protected void onDraw(UI ui, PGraphics pg){
		pg.pushStyle();
		// pg.strokeWeight(5);
		pg.stroke(#ff0000);
		pg.line(0, 0, 0, 1, 0, 0);
		pg.stroke(#00ff00);
		pg.line(0, 0, 0, 0, 1, 0);
		pg.stroke(#0000ff);
		pg.line(0, 0, 0, 0, 0, 1);
		pg.popStyle();
	}
}

public class BillboardText extends UI3dComponent {
	public String text;
	public float x;
	public float y;
	public float z;
	public float s;
	public color c;
	public BillboardText(String text, float x, float y, float z, float s, color c) {
		super();
		this.text = text;
		this.x = x;
		this.y = y;
		this.z = z;
		this.s = s;
		this.c = c;
	}
    @Override
    void onDraw(UI ui, PGraphics pg){
		pg.pushStyle();
		pg.textMode(SHAPE);
		pg.fill(this.c);
		pg.textSize(this.s);
		pg.text(this.text, this.x, this.y, this.z);
		pg.popStyle();
	}
}
