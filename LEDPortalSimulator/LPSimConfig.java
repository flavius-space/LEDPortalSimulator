import java.util.ArrayList;
import java.util.List;
import processing.data.JSONObject;
import processing.data.JSONArray;

public class LPSimConfig {
    public List<LPPanel> panels;
    public List<LPStructure> structures;
    // public float ledSize = (float)1.0;
    public LPSimConfig () {
        panels = new ArrayList<LPPanel>();
        structures = new ArrayList<LPStructure>();
    }
    public void updateFromJSONObject(JSONObject jsonConfig) throws RuntimeException{
        // if(jsonConfig.hasKey("ledSize")) {
        //     this.ledSize = jsonConfig.getFloat("ledSize");
        // }
        if(jsonConfig.hasKey("panels")) {
            JSONArray panelList = jsonConfig.getJSONArray("panels");
            for(int i = 0; i < panelList.size(); i++) {
				LPPanel panel = new LPPanel();
                this.panels.add(panel.updateFromJSONObject(panelList.getJSONObject(i)));
            }
        }
        if(jsonConfig.hasKey("structures")) {
            JSONArray structureList = jsonConfig.getJSONArray("structures");
            for(int i = 0; i < structureList.size(); i++) {
				LPStructure structure = new LPStructure();
                this.structures.add(structure.updateFromJSONObject(structureList.getJSONObject(i)));
            }
        }
    }
}
