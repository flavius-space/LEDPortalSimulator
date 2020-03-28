import java.util.ArrayList;
import java.util.List;
import processing.data.JSONObject;
import processing.data.JSONArray;
import processing.core.PMatrix3D;
import processing.core.PVector;

public class LPPanel {
	public List<PVector> leds;
	public PMatrix3D matrix;
    public LPPanel() {
        leds = new ArrayList<PVector>();
    }
    public LPPanel(List<PVector> leds) {
        this();
        this.leds = leds;
    }
    public LPPanel updateFromJSONObject(JSONObject panelConfig) {
        if(panelConfig.hasKey("pixels")) {
            JSONArray ledList = panelConfig.getJSONArray("pixels");
            for(int i = 0; i < ledList.size(); i++) {
				JSONArray led = ledList.getJSONArray(i);
                this.leds.add(new PVector(led.getInt(0), led.getInt(1), 0));
            }
		}

		if(panelConfig.hasKey("matrix")) {
			JSONArray matrix = panelConfig.getJSONArray("matrix");
			this.matrix = new PMatrix3D(
				matrix.getJSONArray(0).getFloat(0),
				matrix.getJSONArray(0).getFloat(1),
				matrix.getJSONArray(0).getFloat(2),
				matrix.getJSONArray(0).getFloat(3),
				matrix.getJSONArray(1).getFloat(0),
				matrix.getJSONArray(1).getFloat(1),
				matrix.getJSONArray(1).getFloat(2),
				matrix.getJSONArray(1).getFloat(3),
				matrix.getJSONArray(2).getFloat(0),
				matrix.getJSONArray(2).getFloat(1),
				matrix.getJSONArray(2).getFloat(2),
				matrix.getJSONArray(2).getFloat(3),
				matrix.getJSONArray(3).getFloat(0),
				matrix.getJSONArray(3).getFloat(1),
				matrix.getJSONArray(3).getFloat(2),
				matrix.getJSONArray(3).getFloat(3)
			);
		}
        return this;
    }

    public String toString() {
		String out = "Panel:\n";
		out += "-> LEDs:\n\t";
        for(PVector led : this.leds) {
            out += this.leds.toString() + "\n\t";
        }
        return out;
    }
}
