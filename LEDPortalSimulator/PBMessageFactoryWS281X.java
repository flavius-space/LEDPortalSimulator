/**
 * PBMessageFactoryWS281X
 */
public class PBMessageFactoryWS281X extends PBMessageFactoryData{
	public PBMessageFactoryWS281X(final PBColorOrder colorOrder, int channel) {
		super(PBRecordType.SET_CHANNEL_WS2812, channel, 4, colorOrder);
	}
	@Override
	protected int writeBody(byte[] message, int offset, int[] colorIndices, int[] colors) {
		this.validate(colorIndices);
		int i=offset;
		if (debug) System.out.printf(
			"numElements: 0x%02x\ncolorOrders: 0x%02x\n",
			this.colorOrder.numElements,
			this.colorOrder.colorOrder
		);
		message[i++] = (byte) this.colorOrder.numElements;
		message[i++] = (byte) this.colorOrder.colorOrder;
		if (debug) System.out.printf("pixels: 0x%04x\n", colorIndices.length);
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
