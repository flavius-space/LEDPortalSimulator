import java.util.ArrayList;
import java.util.List;
import processing.data.JSONObject;
import processing.data.JSONArray;

public class LPSimConfig {
    public List<LPPanel> panels;
    public LPSimConfig () {
        panels = new ArrayList<LPPanel>();
    }
    public static LPSimConfig fromJSONObject(JSONObject jsonConfig) throws RuntimeException{
        LPSimConfig LPSimConfig = new LPSimConfig();
        if(jsonConfig.hasKey("panels")) {
            JSONArray panelList = jsonConfig.getJSONArray("panels");
            for(int i = 0; i < panelList.size(); i++) {
                LPSimConfig.panels.add(LPPanel.fromJSONObject(panelList.getJSONObject(i)));
            }
        } else {
            throw new RuntimeException("no panels defined in json: " + jsonConfig.toString());
        }
        return LPSimConfig;
    }
}
