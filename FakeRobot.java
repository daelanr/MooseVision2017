package me.daelanroosa.TCPVisionMonitor;

public class FakeRobot {

	public static void main(String[] args) {
		TCPThread TCPThread = new TCPThread();
		TCPThread.start();
		while (true) {
			System.out.println(Double.toString(TCPVisionMonitor.getDist()));
			System.out.println(Double.toString(TCPVisionMonitor.getAngle()));
			System.out.println(Boolean.toString(TCPVisionMonitor.getIsTargetInFrame()));
		}
		

	}

}
