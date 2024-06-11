import time
from machine import I2C

class CHAR_LCD_20_4:
    """
    Interface for communicating with the 20x4 LCD character display over i2c.
    Contains methods and constants for writing to screen and configuring settings.
    """
    # command selection bits send as data to the LCD
    CLEAR_DISPLAY = const(1)
    RETURN_HOME = const(2)
    ENTRY_MODE = const(4)
    DISPLAY_CONTROL = const(8)
    CURSOR_SHIFT = const(16)
    FUNCTION_CONTROL = const(32)
    SET_CGRAM = const(64)
    SET_DDRAM = const(128)

    # parameters for the entry mode command
    ENTRY_RIGHT = const(0)
    ENTRY_LEFT = const(2)
    DISPLAY_SHIFT_ENABLE = const(1)
    DISPLAY_SHIFT_DISABLE = const(0)


    # parameters for the display control command
    DISPLAY_ON = const(4)
    DISPLAY_OFF = const(0)
    CURSOR_ON = const(2)
    CURSOR_OFF = const(0)
    BLINK_ON = const(1)
    BLINK_OFF = const(0)

    # parameters for the cursur shift command
    DISPLAY_MOVE = const(8)
    CURSOR_MOVE = const(0)
    MOVE_RIGHT = const(4)
    MOVE_LEFT = const(0)

    # parameters for the function control command
    BIT_MODE_8 = const(16)
    BIT_MODE_4 = const(0)
    LINES_2 = const(8)
    LINES_1 = const(0)
    DOTS_5X10 = const(4)
    DOTS_5X8 = const(0)

    ENABLE = const(4)
    DATA = const(1)
    COMMAND = const(0)

    # bit used to control the backlight from P3 on the I2C adapter
    BACKLIGHT_ON = const(8)
    BACKLIGHT_OFF = const(0)

    # bit7 = db7
    # bit6 = db6
    # bit5 = db5
    # bit4 = db4
    # bit3 = backlight
    # bit2 = enable
    # bit1 = rw
    # bit0 = rs

    # row 0 ddram addr = 128 to 147
    # row 1 ddram addr = 192 to 211
    # row 2 ddram addr = 148 to 167
    # row 3 ddram addr = 212 to 231

    def __init__(self, i2c : I2C, addr : int) -> None:
        """
        Performs the initialization procedure setting the display to 4 bit mode for i2c communication.

        Parameters
        ----------
        i2c : I2C
            i2c object used to communicate with the display
        addr : int
            i2c address of the display
        """
        self.i2c = i2c
        self.addr = addr
        self.backlight = self.BACKLIGHT_ON

        # each item in the list represents a row containing a sub list of columns
        # self.ddram_map[row][column]
        self.ddram_map = [[], [], [], []]
        for col in range(128, 148):
            self.ddram_map[0].append(col)
        for col in range(192, 212):
            self.ddram_map[1].append(col)
        for col in range(148, 168):
            self.ddram_map[2].append(col)
        for col in range(212, 232):
            self.ddram_map[3].append(col)
        
        # current cursor location
        self.cursor_loc = [0, 0]

        # the current values writen to the display
        self.ddram_value = [[], [], [], []]
        for row in range(0,4):
            for col in range(0, len(self.ddram_map[0])):
                self.ddram_value[row].append(" ")

        # ddram locations that need updating
        self.refresh_loc = []
        
        print("Initializing LCD...")
        time.sleep(1)
        self.write4bits(0 << 4)
        self.write4bits(2 << 4)
        self.clear_display()
        self.set_display_control(self.DISPLAY_ON, self.CURSOR_OFF, self.BLINK_OFF)
        print("LCD initialized")

    def send(self, data : int, mode : int) -> None:
        """
        Used internally to write a byte to the display 4 bits at a time.

        Parameters
        ----------
        data : int
            byte to write to the display
        mode : int
            bits indicating the mode of the display (typically 0 unless sending a command)
        """
        high_nib = data & 0xF0
        low_nib = (data << 4) & 0xF0
        self.write4bits(high_nib | mode)
        self.write4bits(low_nib | mode)

    def write4bits(self, data) -> None:
        """
        Write to the diplay and pulse the enable pin.
        """
        self.write(data)
        self.pulse_enable(data)

    def write(self, data) -> None:
        """
        Write the display, automatically setting the backlight bit.
        """
        self.i2c.writeto(self.addr, bytearray([data | self.backlight]))

    def pulse_enable(self, data) -> None:
        """
        Pulse the enable pin while keeping the other pins constant.
        """
        self.write(data | self.ENABLE)
        self.write(data & ~self.ENABLE)

    def set_backlight(self, enable : bool) -> None:
        """
        Turns the displays backlight on or off.

        Parameters
        ----------
        enable : bool
            True for on, False for off
        """
        if(enable):
            self.backlight = self.BACKLIGHT_ON
        else:
            self.backlight = self.BACKLIGHT_OFF
        self.send(0, self.COMMAND)

    def clear_display(self) -> None:
        """
        Send the clear display command erasing all characters from the screen.
        """
        self.send(self.CLEAR_DISPLAY, self.COMMAND)
        self.cursor_loc = [0, 0]
        self.refresh_loc.clear()
        time.sleep(0.01)

    def return_home(self) -> None:
        """
        Send the return home command setting the cursor location to the top left of the display.
        """
        self.send(self.RETURN_HOME, self.COMMAND)
        self.cursor_loc = [0, 0]
        time.sleep(0.01)

    def set_entry_mode(self, dir : int, shift : int) -> None:
        """
        Send the entry mode command setting the direction that text is written to the
        screen and if the cursor is automatically shifted.

        Parameters
        ----------
        dir : int
            ENTRY_RIGHT or ENTRY_LEFT
        shift : int
            DISPLAY_SHIFT_ENABLE or DISPLAY_SHIFT_DISABLE
        """
        data = self.ENTRY_MODE | dir | shift
        self.send(data, self.COMMAND)

    def set_display_control(self, dis : int, cur : int, blink : int) -> None:
        """
        Send the display control command setting the display enabled, cursor enabled,
        and blink enabled settings.

        Parameters
        ----------
        dis : int
            DISPLAY_ON or DISPLAY_OFF
        cur : int
            CURSOR_ON or CURSOR_OFF
        blink : int
            BLINK_ON or BLINK_OFF
        """
        data = self.DISPLAY_CONTROL | dis | cur | blink
        self.send(data, self.COMMAND)

    def set_cursur_shift(self, disp_cursor : int, dir : int) -> None:
        """
        Send the cursor shift command shift the cursor or display left or right.
        For memory mapping the increment and decrement cursor functions should be
        used instead.

        Parameters
        ----------
        disp_cursor : int
            DISPLAY_MOVE or CURSOR_MOVE
        dir : int
            MOVE_RIGHT or MOVE_LEFT
        """
        data = self.CURSOR_SHIFT | disp_cursor | dir
        self.send(data, self.COMMAND)

    def set_function_control(self, bit_mode : int, lines : int, dots : int) -> None:
        """"
        Send the function control command setting bit mode, number of lines, character dot size.

        Parameters
        ----------
        bit_mode : int
            BIT_MODE_8 or BIT_MODE_4
        lines : int
            LINES_2 or LINES_1
        dots : int
            DOTS_5X10 or DOTS_5X8
        """
        data = self.FUNCTION_CONTROL | bit_mode | lines | dots
        self.send(data, self.COMMAND)

    def set_cgram_addr(self, addr : int) -> None:
        """
        Send the set CGRAM address command setting the pointer register to a CGRAM location.
        Writing data to the CGRAM location will create a custom character.

        Parameters
        ----------
        addr : int
            CGRAM address
        """
        data = self.SET_CGRAM | addr
        self.send(data, self.COMMAND)

    def set_ddram_addr(self, addr : int) -> None:
        """
        Send the set DDRAM address command setting the pointer register to a DDRAM location.
        Data that is written to DDRAM should be the CGRAM address of the character to display.

        Parameters
        ----------
        addr : int
            DDRAM address
        """
        data = self.SET_DDRAM | addr
        self.send(data, self.COMMAND)

    def write_ram(self, data : int) -> None:
        """
        Write data to the memory location of the current address stored in the pointer register.
        Writing to CGRAM will create a custom character.
        Writing the CGRAM address of a character to DDRAM to display that character to the screen.
        """
        self.send(data, self.DATA)

    def refresh(self) -> None:
        """
        Refreshes the display using the resfresh_loc list to only update
        values that need to be updated.
        """
        for loc in self.refresh_loc:
            self.set_ddram_addr(self.ddram_map[loc[0]][loc[1]])
            self.write_ram(self.ddram_value[loc[0]][loc[1]])
        self.refresh_loc.clear()
    
    def set_row(self, row :  int, text : str, wrap=False) -> None:
        """
        Sets a row in the ddram_map and updates the refresh_loc list.

        Parameters
        ----------
        row : int
            row number 0 - 3
        text : str
            only uses first 20 characters
        wrap : bool
            if true wrap to next row (not yet implemented)
        """
        text = "{:20}".format(text)
        
        for col in range(0, 20):
            if(ord(text[col]) != self.ddram_value[row][col]):
                self.ddram_value[row][col] = ord(text[col])
                self.refresh_loc.append([row, col])
