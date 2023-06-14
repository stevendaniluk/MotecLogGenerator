import cantools
import math

class DataLog(object):
    """ Container for storing log data which contains a set of channels with time series data."""
    def __init__(self, name=""):
        self.name = name
        self.channels = {}

    def clear(self):
        self.channels = {}

    def add_channel(self, name, units, data_type, decimals, initial_message=None):
        msg = [] if not initial_message else [initial_message]
        self.channels[name] = Channel(name, units, data_type, decimals, msg)

    def start(self):
        """ Returns the earliest timestamp from all existing channels [s]. """
        t = math.inf
        for name, channel in self.channels.items():
            t = min(t, channel.start())

        if t != math.inf:
            return t
        else:
            return 0.0

    def end(self):
        """ Returns the latest timestamp from all existing channels [s]. """
        end = 0
        for name, channel in self.channels.items():
            end = max(end, channel.end())

        return end

    def duration(self):
        """ Returns the duration of the log [s]. """
        return self.end() - self.start()

    def resample(self, frequency):
        """ Resamples all channels such that all messages occur at a fixed frequency.

        See the resample method of the Channel class for more details.
        """
        start = self.start()
        end = self.end()
        for channel_name in self.channels:
            self.channels[channel_name].resample(start, end, frequency)

    def from_can_log(self, log_lines, can_db):
        """ Creates channels populated with messages from a candump file and can database.

        This will create a channel for each entry in the database that has messages present in the
        log.

        log_lines: List, containing candump log lines (recorded with 'candump' with '-l')
        can_db: cantools.database
        """
        self.clear()

        # Cache all the frame ids in the database for quick lookups
        known_ids = set()
        for msg in can_db.messages:
            known_ids.add(msg.frame_id)

        for line in log_lines:
            stamp, bus, id, data = self.__parse_can_log_line(line)

            if id not in known_ids:
                continue

            db_msg = can_db.get_message_by_frame_id(id)
            msg_decoded = can_db.decode_message(id, data)

            for msg, signal in zip(msg_decoded.items(), db_msg.signals):
                name = msg[0]
                value = msg[1]

                if name in self.channels:
                    self.channels[name].messages.append(Message(stamp, value))
                else:
                    self.add_channel(name, signal.unit, float, 3, Message(stamp, value))

    def from_csv_log(self, log_lines):
        """ Creates channels populated with messages from a CSV log file.

        This will create a channel for each column in the CSV file, with the name of that channel
        taken from the CSV header. All channels will be created without any units. Any non numeric data
        will be ignored, and that channel will be removed. The first column of data must be time

        log_lines: List, containing CSV log lines
        """
        self.clear()

        if not log_lines:
            return

        # Get the channel names, ignore the first column as it is assumed to be time
        header = log_lines[0]
        channel_names = header.split(",")[1:]

        # We'll keep a map of names and column numbers for easy channel lookups when parsing rows
        i = 0
        channel_dict = {}
        for name in channel_names:
            self.add_channel(name, "", float, 0)

            channel_dict[name] = i
            i += 1

        # Go through each line grabbing all the channel values
        for line in log_lines[1:]:
            line = line.strip("\n")
            values = line.split(",")

            # Timestamp is the first element
            t = float(values[0])

            # Grab each remaining channel value. We keep a map of all the channel names and column
            # numbers we are retrieving, so we will look at that to determine which columns to read.
            # If we fail to read an entry in any column, we will delete that channel entirely.
            invalid_channels = []
            for name, i in channel_dict.items():
                # We'll only parse numeric data
                try:
                    val = float(values[i + 1])
                    message = Message(t, val)
                    self.channels[name].messages.append(message)

                    val_text_split = values[i + 1].split(".")
                    decimals_present = 0 if len(val_text_split) == 1 else len(val_text_split[1])
                    self.channels[name].decimals = max(decimals_present, self.channels[name].decimals)
                except ValueError:
                    print("WARNING: Found non numeric values for channel %s, removing channel" % \
                        name)
                    invalid_channels.append(name)

            for name in invalid_channels:
                del channel_dict[name]
                del self.channels[name]

    def from_accessport_log(self, log_lines):
        """ Creates channels populated with messages from a COBB Accessport CSV log file.

        This will create a channel for each column in the CSV file, with the name and units of that
        channel taken from the CSV header. Any non numeric data will be ignored, and that channel
        will be removed.

        log_lines: List, containing CSV log lines
        """

        self.from_csv_log(log_lines)

        # Accessport logs have a column for AP info which is not of any value so we'll delete it
        for key in self.channels.keys():
            if "AP Info" in key:
                del self.channels[key]
                break

        # Update all the channel names and units
        for channel_name, channel in self.channels.items():
            # Channels have the format "Name (Units)"
            print(channel_name)
            name, units = channel_name.split(" (")
            units = units[:-1]

            channel.name = name
            channel.units = units

    @staticmethod
    def __parse_can_log_line(line):
        """ Extracts the timestamp, bus, arbitration id, and data from a single line in a can log file
        recorded with candump -l.
        """
        stamp, bus, msg = line.split()
        stamp = float(stamp[1:-1])
        id, data = msg.split("#")
        id = int(id, 16)
        data = bytearray.fromhex(data)

        return stamp, bus, id, data

    def __str__(self):
        output = "Log: %s, Duration: %f s" % (self.name, (self.end() - self.start()))
        for channel_name, channel_data in self.channels.items():
            output += "\n\t%s" % channel_data
        return output

class Channel(object):
    """ Represents a singe channel of data containing a time series of values."""
    def __init__(self, name, units, data_type, decimals, messages=None):
        self.name = str(name)
        self.units = str(units)
        self.data_type = data_type
        self.decimals = decimals
        if messages:
            self.messages = messages
        else:
            self.messages = []

    def start(self):
        if self.messages:
            return self.messages[0].timestamp
        else:
            return 0

    def end(self):
        if self.messages:
            return self.messages[-1].timestamp
        else:
            return 0

    def avg_frequency(self):
        """ Computes the average frequency from the samples based on the duration of the channel
        and the number of messages"""
        if len(self.messages) >= 2:
            dt = self.end() - self.start()
            return len(self.messages) / dt
        else:
            return 0

    def resample(self, start_time, end_time, frequency):
        """ Resamples the data such that all messages occur at a fixed frequency.

        If multiple messages fall within the time interval between messages for the new frequency,
        the latest message will be used. When no existing messages fall within the time interval
        the most recent value will be retained. If no existing message is present within the first
        new time interval, then the first message will be initialized at 0.
        """
        if not self.messages:
            return

        # Determine how many messages this channel should have,
        num_msgs = math.floor(frequency * (end_time - start_time))
        dt_step = 1.0 / frequency

        # Create a new message at each time new time point based on the frequency. As we step
        # through the new sample points we'll find the latest pre existing message to insert there,
        # and will hold that value until we find another message.
        value = 0
        t = start_time
        current_msgs_index = 0
        new_msgs = []
        for i in range(num_msgs):
            # Grab the latest message that falls in this time window, if there is one, and update
            # the current channel value
            while current_msgs_index < len(self.messages):
                msg_stamp = self.messages[current_msgs_index].timestamp

                if msg_stamp < t + 0.5 * dt_step:
                    # This message falls in the time window
                    value = self.messages[current_msgs_index].value
                    current_msgs_index += 1
                else:
                    # This messages belongs in a future window
                    break

            new_msgs.append(Message(t, value))
            t += dt_step

        self.messages = new_msgs

    def __str__(self):
        return "Channel: %s, Units: %s, Decimals: %d, Messages: %d, Frequency: %.2f Hz" % \
        (self.name, self.units, self.decimals, len(self.messages), self.avg_frequency())

class Message(object):
    """ A single message in a time series of data. """
    def __init__(self, timestamp=0, value=0):
        self.timestamp = float(timestamp)
        self.value = float(value)

    def __str__(self):
        return "t=%f, value=%f" % (self.timestamp, self.value)
