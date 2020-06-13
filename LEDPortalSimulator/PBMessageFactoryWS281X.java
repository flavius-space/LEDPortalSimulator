import java.util.logging.Logger;

/**
 * PBMessageFactoryWS281X
 */
public class PBMessageFactoryWS281X extends PBMessageFactoryData{
	private static final Logger logger = Logger.getLogger(PBMessageFactoryWS281X.class.getName());
	public PBMessageFactoryWS281X(final PBColorOrder colorOrder, int channel) {
		super(PBRecordType.SET_CHANNEL_WS2812, channel, 4, colorOrder);
	}
	@Override
	protected int writeBody(byte[] message, int offset, int[] colorIndices, int[] colors) {
		this.validate(colorIndices);
		int i=offset;
		logger.fine(String.format(
			"numElements: 0x%02x\ncolorOrders: 0x%02x\n",
			this.colorOrder.numElements,
			this.colorOrder.colorOrder
		));
		message[i++] = (byte) this.colorOrder.numElements;
		message[i++] = (byte) this.colorOrder.colorOrder;
		logger.fine(String.format("pixels: 0x%04x\n", colorIndices.length));
		for(byte b : LPByteUtils.uint16LEBytes(colorIndices.length)) {
			message[i++] = b;
		}
		for(int colorIdx : colorIndices) {
			for(byte b : this.colorOrder.colorBytes(colors[colorIdx])) {
				message[i++] = b;
			}
		}
		return (i - offset);
	}
}
