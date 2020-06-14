import java.util.ArrayList;
import java.util.List;
import java.util.logging.Logger;

import processing.data.JSONObject;
import processing.data.JSONArray;
import processing.core.PMatrix3D;
import processing.core.PVector;

public class LPSimConfig {
	private static final Logger logger = Logger.getLogger(LPMeshable.class.getName());
    public List<LPPanel> panels = new ArrayList<LPPanel>();
    public List<LPStructure> structures = new ArrayList<LPStructure>();;
    public List<LPStructure> debugStructures = new ArrayList<LPStructure>();;
    // public float ledSize = (float)1.0;
    public LPSimConfig () {}
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

	public PVector getWorldCentroid() {
		PVector position = new PVector(0, 0, 0);
		List<PVector> centroids = new ArrayList<PVector>();
		for(LPPanel panel : this.panels) {
			centroids.add(panel.getWorldCentroid());
		}
		return LPMeshable.getCentroid(centroids);
	}

	public PMatrix3D getWorldCentroidMatrix() {
		PVector centroid = this.getWorldCentroid();
		PMatrix3D matrix = new PMatrix3D();
		matrix.translate(centroid.x, centroid.y, centroid.z);
		return matrix;
	}
}
