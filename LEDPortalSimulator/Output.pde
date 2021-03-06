import java.util.Arrays;
import processing.serial.*;
import java.util.logging.Logger;

static abstract class LPSerialOutput extends LXOutput {
	private static final Logger logger = Logger.getLogger(LPSerialOutput.class.getName());
	public static HashMap<String, Serial> ports = new HashMap();
	protected String serialPort;

	public LPSerialOutput(LX lx, PApplet parent, String serialPort, int baudRate) {
		super(lx, serialPort);
		this.serialPort = serialPort;
		if(!ports.containsKey(serialPort)) ports.put(serialPort, new Serial(parent, serialPort, baudRate));
	}

	public void write(byte[] message) {
		int i = 0;
		for (byte b: message) {
			logger.fine(String.format("message[%03d] = 0x%02x\n", i++, b));
		}
		ports.get(this.serialPort).write(message);
	}
}

// TODO: upgrade to the latest LX way of doing things when it's released
public static int[] allPoints(LX lx) {
	int[] points = new int[lx.total];
	for (int i = 0; i < points.length; ++i) {
		points[i] = i;
	}
	return points;
}

abstract public class PixelBlazeExpanderOutput extends LPSerialOutput {
	// TODO: only one instance per serial device
	public final List<PBMessageFactory> messageFactories;
	public static final int baudRate = 2000000;
	public int channelNumber;
	public int[] colorIndices;

	public PixelBlazeExpanderOutput(LX lx, PApplet parent, String serialPort, int channelNumber, int[] colorIndices) {
		super(lx, parent, serialPort, baudRate);
		this.colorIndices = colorIndices;
		this.channelNumber = channelNumber;
		this.messageFactories = new ArrayList<PBMessageFactory>();
	}

	@Override
	protected void onSend(int[] colors) {
		for(PBMessageFactory messageFactory : this.messageFactories) {
			this.write(messageFactory.getMessage(this.colorIndices, colors));
		}
	}
}

public class PixelBlazeExpanderParentOutput extends PixelBlazeExpanderOutput {
	public PixelBlazeExpanderParentOutput(LX lx, PApplet parent, String serialPort) {
		super(lx, parent, serialPort, 0, new int[]{});
	}
}

public class PixelBlazeExpanderSendAllOutput extends PixelBlazeExpanderOutput {
	public PixelBlazeExpanderSendAllOutput(LX lx, PApplet parent, String serialPort) {
		super(lx, parent, serialPort, 0, new int[]{});
		this.messageFactories.add(new PBMessageFactoryDrawAll());
	}
}

public class PixelBlazeExpanderWS281XOutput extends PixelBlazeExpanderOutput {
	public PixelBlazeExpanderWS281XOutput(LX lx, PApplet parent, String serialPort, int channelNumber, int[] colorIndices) {
		super(lx, parent, serialPort, channelNumber, colorIndices);
		this.messageFactories.add(0, new PBMessageFactoryWS281X(PBColorOrder.RGB, this.channelNumber));
	}

	public PixelBlazeExpanderWS281XOutput(LX lx, PApplet parent, String serialPort, int channelNumber, LXFixture fixture) {
		this(lx, parent, serialPort, channelNumber, LXFixture.Utils.getIndices(fixture));
	}

	public PixelBlazeExpanderWS281XOutput(LX lx, PApplet parent, String serialPort, int channelNumber) {
		this(lx, parent, serialPort, channelNumber, allPoints(lx));
	}
}


public class PixelBlazeExpanderAPA102DataOutput extends PixelBlazeExpanderOutput {
	public PixelBlazeExpanderAPA102DataOutput(LX lx, PApplet parent, String serialPort, int channelNumber, int freq, int[] colorIndices) {
		super(lx, parent, serialPort, channelNumber, colorIndices);
		this.messageFactories.add(0, new PBMessageFactoryAPA102Data(PBColorOrder.RGBV, this.channelNumber, freq));
	}

	public PixelBlazeExpanderAPA102DataOutput(LX lx, PApplet parent, String serialPort, int channelNumber, int freq, LXFixture fixture) {
		this(lx, parent, serialPort, channelNumber, freq, LXFixture.Utils.getIndices(fixture));
	}

	public PixelBlazeExpanderAPA102DataOutput(LX lx, PApplet parent, String serialPort, int channelNumber, int freq) {
		this(lx, parent, serialPort, channelNumber, freq, allPoints(lx));
	}
}

public class PixelBlazeExpanderAPA102ClockOutput extends PixelBlazeExpanderOutput {
	public PixelBlazeExpanderAPA102ClockOutput(LX lx, PApplet parent, String serialPort, int channelNumber, int freq) {
		super(lx, parent, serialPort, 0, new int[]{});
		this.messageFactories.add(0, new PBMessageFactoryAPA102Clock(channelNumber, freq));
	}
}
