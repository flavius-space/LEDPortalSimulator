import java.util.ArrayList;
import java.util.List;
import processing.data.JSONObject;
import processing.data.JSONArray;
import processing.core.PMatrix3D;
import processing.core.PVector;

public class LPPanel extends LPMeshable {
	public List<PVector> leds;
    public LPPanel() {
        leds = new ArrayList<PVector>();
    }
    public LPPanel(List<PVector> leds) {
        this();
        this.leds = leds;
    }
    public LPPanel updateFromJSONObject(JSONObject jsonConfig) {
		super.updateFromJSONObject(jsonConfig);
        if(jsonConfig.hasKey("pixels")) {
            JSONArray ledList = jsonConfig.getJSONArray("pixels");
            for(int i = 0; i < ledList.size(); i++) {
				JSONArray led = ledList.getJSONArray(i);
                this.leds.add(new PVector(led.getInt(0), led.getInt(1), 0));
            }
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

	public List<PVector> getWorldLEDs() {
		List<PVector> worldLEDs = new ArrayList<PVector>();
		for(PVector led : this.leds) {
			worldLEDs.add(getWorldCoordinate(this.matrix, led));
		}
		return worldLEDs;
	}


}
