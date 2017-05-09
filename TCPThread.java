package me.daelanroosa.TCPVisionMonitor;

import java.io.IOException;

public class TCPThread extends Thread{
	
	public void run() {
		try {	
			TCPVisionMonitor.visionMonitor();
		} catch (IOException e){
			System.out.println("ouch");
		}

	}
}
