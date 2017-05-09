package me.daelanroosa.TCPVisionMonitor;

import java.io.*;

import java.net.*;
import java.util.*;
import java.util.concurrent.ConcurrentLinkedQueue;

/** 
 * TCP client for communicating with an external TCP server running on a coprocessor to facilitate vision processing for FRC team 1391.
 * @author daelan
 *
 */
public class TCPVisionMonitor {
	//sets server IP and port
	private static String addr = "127.0.0.1";
	private static int port = 5011;
	
	//instantiates variables for the values to be pulled from the server
	private static double dist = 0.0;
	private static double angle = 0.0;
	private static boolean isTargetInFrame = false;
	
	//creates necessary locks for threadsafing
	private static final Object distLock = new Object();
	private static final Object angleLock = new Object();
	private static final Object isTargetInFrameLock = new Object();
	
	//Queues commands to be sent over TCP socket
	private static Queue<String> queryQueue = new ConcurrentLinkedQueue<String>();
	
	//instantiates variables used in the parsing sequence
	//Does it work? Yes. Do I know why it works? No. Do I particularly care why it works? FUCK no.
	private static String dataSet = "empty set";
	private static String[] variables;
	
	public static void visionMonitor() throws IOException {
		//Loops continuously to automatically reconnect. 
		//connectSocket() runs until connection is made, socketReader() terminates upon throwing an exception
		//After terminating socketReader(), socket is closed, and loop restarts
		while (true) {
			//instantiates new socket, with the socket manager method 
			Socket socket = connectSocket(addr, port);
			
			//instantiates output stream to socket
			DataOutputStream toServer = new DataOutputStream(socket.getOutputStream());
			//instantiates socket reader
			BufferedReader fromServer = new BufferedReader(new InputStreamReader(socket.getInputStream()));
			
			//pings server, and then reads server response. NOTE: Server response must end in "\n" or the readLine() method WILL hang
			socketReader(toServer, fromServer);
			
			//checkpoint for debugging
			System.out.println("ah zombies");
			
			//closes socket, prevents zombie sockets from hogging ports
			socket.close();
		}
	}
	
	private static Socket connectSocket(String addr, int port) throws ConnectException, IOException {
		//While loop attempts connection until connection completes
		while (true) {
			//try statement handles exceptions raised when connection fails
			try {
				//attempts to create and return new socket object
				Socket socket = new Socket(addr, port);
				return socket;
			} catch (ConnectException e){
				//alert for connection failure
				System.out.println("Connection Refused");
				System.out.println(e.getMessage());
			}
		}
	}
	
	private static void socketReader(DataOutputStream toServer, BufferedReader fromServer) throws IOException{
		
		while (dataSet != "break") {
			//try statement handles broken pipe exceptions, etc
			try {	
				//checkpoint for debugging
				System.out.println("querying...");
				
				//Checks to see whether any commands are queued. Cycles through the queue until all have been sent and confirmed recieved
				String query = queryQueue.poll();
				while (query != null) {
					toServer.writeBytes(query);
					
					//This line isn't strictly necessary, but it ensures that client and server remain in phase
					String serverResponse = fromServer.readLine();
					
					query = queryQueue.poll();
				}
				
				//queries python TCP server with key character
				//currently only a query for vision values is implemented, but this could be expanded to include other commands
				toServer.writeBytes("q");
				
				//checkpoint for debugging
				System.out.println("q");
				
				//reads python server response (see note above)
				dataSet = fromServer.readLine();
				
				//check to see that server responded, then parses response
				if (dataSet != null){
					variables = dataSet.split(":");
					
					System.out.println("Data received");
					
					//assigns variables based in info returned from server
					if (variables.length >= 3){
						 
						System.out.println("data satisfies length");
						
						//checkpoint for debugging
						System.out.println(variables[0] + " " + variables[1] + " " + variables[2]);
						
						//assigns variables as statics, synchronized for threadsafing
						synchronized (TCPVisionMonitor.distLock) {
							dist = Double.parseDouble(variables[0]);
						}
						
						synchronized (TCPVisionMonitor.angleLock) {
							angle = Double.parseDouble(variables[1]);
						}
						
						synchronized (TCPVisionMonitor.isTargetInFrameLock) {
							if (variables[2] == "1"){
								isTargetInFrame = true;
							} else {
								isTargetInFrame = false;
							}
						}
					} else {
						System.out.println("null data");
					}
				}
		
			} catch (SocketException e) {
				//terminates method on exception, allowing the control method to loop back and call the connection method
				break;
			}
		}
	}
	
	//Threadsafe methods to access vision values
	public static double getDist() {
		synchronized (TCPVisionMonitor.distLock) {
			return TCPVisionMonitor.dist;
		}
	}
	
	public static double getAngle() {
		synchronized (TCPVisionMonitor.angleLock) {
			return angle;
		}
	}
	
	public static boolean getIsTargetInFrame() {
		synchronized (TCPVisionMonitor.isTargetInFrameLock) {
			return isTargetInFrame;
		}
	}
	
	//Adds command to queue of commands to be sent over TCP socket
	public static void addCommand(String command) {
		queryQueue.offer(command);
	}
}
