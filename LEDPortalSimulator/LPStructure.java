import java.util.ArrayList;
import java.util.List;
import processing.data.JSONObject;
import processing.data.JSONArray;
import processing.core.PMatrix3D;
import processing.core.PVector;

public class LPStructure extends LPMeshable {
	public String type;

    public LPStructure updateFromJSONObject(JSONObject jsonConfig) {
		super.updateFromJSONObject(jsonConfig);
		if(jsonConfig.hasKey("type")) {
			this.type = jsonConfig.getString("type");
		}
        return this;
	}
}
