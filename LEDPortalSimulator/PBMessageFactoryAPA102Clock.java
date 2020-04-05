/**
 * PBMessageFactoryAPA102Clock
 */
public class PBMessageFactoryAPA102Clock extends PBMessageFactory{
	public final long freq;
	public PBMessageFactoryAPA102Clock(int channel, long freq) {
		super(PBRecordType.SET_CHANNEL_APA102_CLOCK, channel, 4, 0);
		this.freq = freq;
	}
	@Override
	protected int writeBody(byte[] message, int offset, int[] colorIndices, int[] colors) {
		int i=offset;
		if (debug) System.out.printf("freq: 0x%08x (%dd)\n", this.freq, this.freq);
		for(byte b : LPByteUtils.uint32LEBytes(this.freq)) {
			message[i++] = b;
		}
		return (i - offset);
	}
}
