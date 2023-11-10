#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <fcntl.h>
#include <unistd.h>
#include <linux/i2c-dev.h>
#include <sys/ioctl.h>
#include <math.h>

void snooze(double t) {
    struct timespec req = {t, fmod(t, 1.0) * 1E9};
    nanosleep(&req, NULL);
}


int main()
{
	int file;
	char data;
	char high= 0x00;
	char low = 0x7D;
	time_t rawtime;
	struct tm *timeinfo;
 
	// Open I2C1 for reading the sound meter module registers
	if ((file = open("/dev/i2c-1", O_RDWR)) < 0)
	{
		perror("Failed to open I2C1!");
		exit(1);
	}
	
	// 0x48 is the decibel meter I2C address
	if (ioctl  (file, I2C_SLAVE, 0x48) < 0)
	{
		perror ("db Meter module is not connected/recognized at I2C addr = 0x48");
		close (file);
		exit (1);
	}

	data = 0x07;
	if (write (file, &data, 1) != 1)
	{
		
		perror ("Failed to write register 0x07");
		close (file);
		exit (1);
	}
	else
	{
		write (file, &high, 1);
	}
	
	data = 0x08;
	if (write (file, &data, 1) != 1)
	{
		perror ("Failed to write register 0x08");
		close (file);
		exit (1);
	}
	else
	{
		write (file, &low, 1);
	}

	

	while (1)
	{
		// Decibel value is stored in register 0x0A
		data = 0x0A;
		if (write (file, &data, 1) != 1)
		{
			perror ("Failed to write register 0x0A");
			close (file);
			exit (1);
		}
		 
		if (read (file, &data, 1) != 1)
		{
			perror ("Failed to read register 0x0A");
			close (file);
			exit (1);
		}
		 
		time (&rawtime);
		timeinfo = localtime (&rawtime);
		 
		printf ("%sSound level: %d dB SPL\r\n\r\n", asctime(timeinfo), data);

		snooze(0.125);
	}
	
	close (file);
	return 0;
}