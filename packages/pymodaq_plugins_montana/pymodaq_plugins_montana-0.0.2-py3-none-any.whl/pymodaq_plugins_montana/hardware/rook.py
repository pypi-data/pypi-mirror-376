#!/usr/bin/env python3
#

import sys
import os
from pymodaq_plugins_montana.hardware import instrument
import time
import datetime


class Rook(instrument.Instrument):
    def __init__(self, ip, version='v1', verbose=False, tunnel=False, port=instrument.Rest_Ports.lynx_hlm):
        super().__init__(ip=ip,
                         port=port,
                         version=version,
                         verbose=verbose,
                         tunnel=tunnel)

    #
    # Controller commands
    #
    def emergency_stop(self):
        '''Stop all axes'''
        self.call_method(f'controller/methods/emergencyStop()')
        return

    #
    # per-Axis commands
    #
    def get_axis_status(self, stack_num, axis_num):
        """Get the real-time status of the axis"""
        r = self.get_prop(f'stacks/stack{stack_num}/axes/axis{axis_num}/properties/status')
        return r['status']

    def get_axis_moving(self, stack_num, axis_num):
        return self.get_axis_status(stack_num, axis_num)['moving']

    def get_axis_target_position(self, stack_num, axis_num):
        '''Get the target position for the given axis.'''
        return self.get_axis_status(stack_num, axis_num)['targetPosition']

    def get_axis_encoder_position(self, stack_num, axis_num):
        '''Get the encoder position for the given axis.'''
        return self.get_axis_status(stack_num, axis_num)['encoderPosition']

    def wait_for_axis_not_moving(self, stack_num, axis_num, max_wait=datetime.timedelta(seconds=60)):
        """Returns True if the axis reached the target before timeout, False
           if timeout occurred and axis was still moving."""

        reached_target = False
        start_time  = datetime.datetime.now()
        while not reached_target:
            # Delay to give time for last move command to begin and
            # state to propogate through system
            time.sleep(0.5)

            reached_target = not self.get_axis_moving(stack_num, axis_num)

            # Break if we've exceeded the max_wait
            elapsed_time = datetime.datetime.now() - start_time
            if not reached_target and elapsed_time > max_wait:
                self.stop_axis(stack_num, axis_num)
                print(f'Timed out before reaching target, stopped axis {axis_num}.')
                break

        return reached_target

    def set_axis_velocity(self, stack_num: int, axis_num: int, velocity: float):
        '''Set the target velocity of the given axis

        velocity in m/s
        '''
        self.set_prop(f'stacks/stack{stack_num}/axes/axis{axis_num}/properties/velocity', velocity)
        return

    def get_axis_velocity(self, setack_num, axis_num) -> float:
        return self.get_prop(f'stacks/stack{stack_num}/axes/axis{axis_num}/properties/velocity')['velocity']

    def move_axis_to_negative_limit(self, stack_num, axis_num, wait=False):
        '''Move axis to the negative limit'''
        self.call_method(f'stacks/stack{stack_num}/axes/axis{axis_num}/methods/moveToNegativeLimit()')
        if wait: self.wait_for_axis_not_moving(stack_num, axis_num)
        return

    def move_axis_to_positive_limit(self, stack_num, axis_num, wait=False):
        '''Move axis to the positive limit'''
        self.call_method(f'stacks/stack{stack_num}/axes/axis{axis_num}/methods/moveToPositiveLimit()')
        if wait: self.wait_for_axis_not_moving(stack_num, axis_num)
        return

    def move_axis_absolute_position(self, stack_num, axis_num, pos, wait=False):
        """Move axis to an absolute position

        Parameter
        ---------
        pos: float
            position in meter
        """
        self.call_method(f'stacks/stack{stack_num}/axes/axis{axis_num}/methods/moveAbsolute(double:pos)', pos)
        if wait: self.wait_for_axis_not_moving(stack_num, axis_num)
        return

    def jog_axis(self, stack_num, axis_num, move_positive_direction):
        '''Jog axis continuously in one direction with no target position'''
        direction = 'Positive' if move_positive_direction else 'Negative'
        self.call_method(f'stacks/stack{stack_num}/axes/axis{axis_num}/methods/jog(JogDirection:dir)', direction)
        return

    def stop_axis(self, stack_num, axis_num):
        '''Stop an axis'''
        self.call_method(f'stacks/stack{stack_num}/axes/axis{axis_num}/methods/stop()')
        return

    def zero_axis(self, stack_num, axis_num):
        '''Zero the encoder position of an axis'''
        self.call_method(f'stacks/stack{stack_num}/axes/axis{axis_num}/methods/zero()')
        return

    def set_axis_closed_loop(self, stack_num, axis_num, cl_enabled):
        '''Enable/disable closed loop feedback mode'''
        direction = 'ClosedLoop' if cl_enabled else 'OpenLoop'
        self.set_prop(f'stacks/stack{stack_num}/axes/axis{axis_num}/properties/feedbackMode', direction)
        return

    def set_axis_closed_loop_deadband_counts(self, stack_num, axis_num, counts):
        '''Set the closed-loop deadband encoder counts'''
        self.set_prop(f'stacks/stack{stack_num}/axes/axis{axis_num}/properties/closedLoopDeadbandCounts', counts)
        return

    def set_axis_closed_loop_deadband_timeout(self, stack_num, axis_num, timeout):
        '''Set the closed-loop deadband encoder timeout'''
        self.set_prop(f'stacks/stack{stack_num}/axes/axis{axis_num}/properties/closedLoopDeadbandTimeout', timeout)
        return
    
    def set_axis_hard_stop_detection_enabled(self, stack_num, axis_num, enabled):
        '''Enable/disable hard stop detection'''
        self.set_prop(f'stacks/stack{stack_num}/axes/axis{axis_num}/properties/hardStopDetectionEnabled', enabled)
        return
        
    def set_axis_hard_stop_rebound_distance(self, stack_num, axis_num, distance):
        '''Set the hardstop rebound distance'''
        self.set_prop(f'stacks/stack{stack_num}/axes/axis{axis_num}/properties/hardStopReboundDistance', distance)
        return
        
    def set_axis_hard_stop_sensitivity(self, stack_num, axis_num, sensitivity):
        '''Set the hardstop detection sensitivity'''
        self.set_prop(f'stacks/stack{stack_num}/axes/axis{axis_num}/properties/hardStopSensitivity', sensitivity)
        return


if __name__ == "__main__":

    rook = Rook('10.35.3.38', verbose=False)

    stack_num = 1
    axis_num  = 1

    for p in [0, 100, 200, 300, 400, 500, 0]: # um
        print(f'Move absolute to {p}')
        rook.move_axis_absolute_position(stack_num, axis_num, p/1000/1000)
        if rook.wait_for_axis_not_moving(stack_num, axis_num):
            print('Target acquired.')
        else:
            print('Failed to acquire target before timeout occurred.')
