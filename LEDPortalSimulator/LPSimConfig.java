import java.util.ArrayList;
import java.util.List;
import processing.data.JSONObject;
import processing.data.JSONArray;
import processing.core.PMatrix3D;
import processing.core.PVector;

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
	public PMatrix3D getPanelMatrixAverage() {
		PVector position = new PVector(0, 0, 0);
		// PVector normal = new PVector(0, 0, 1);
		PMatrix3D matrix = new PMatrix3D();
		int nVertices = 0;
		for(LPPanel panel : this.panels) {
			for(PVector vertex: panel.getWorldVertices()) {
				System.out.printf("position: %s, vertex: %s\n", position, vertex);
				// position = position.mult((float)nVertices/(nVertices + 1));
				// vertex = vertex.mult((float)1/(nVertices + 1));
				// System.out.printf("scaled position: %s, vertex: %s\n", position, vertex);
				position = position.add(vertex);
				nVertices++;
			}
		}
		position.div(nVertices);
		System.out.printf("final position %s", position);
		matrix.translate(position.x, position.y, position.z);
		return matrix;
	}
}
