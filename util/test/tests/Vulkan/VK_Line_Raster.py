import rdtest
import renderdoc as rd


class VK_Line_Raster(rdtest.TestCase):
    demos_test_name = 'VK_Line_Raster'

    # Line segments are relative to 100x75 framebuffers. We sample in each corner (adjusted to be sure even with
    # slightly varying rasterization we should sample in the line endpoint) and in the middle
    points = [
           [ 6,  69 ],
           [ 50, 36 ],
           [ 93, 5  ],
        ]

    view = [ 100, 75 ]

    def sample(self, row, col):
        ret = []
        for p in self.points:
            x = self.view[0] * col + p[0]
            y = self.view[1] * row + p[1]

            picked: rd.PixelValue = self.out.PickPixel(self.tex.resourceId, False, x, y, 0, 0, 0)
            ret.append(rdtest.value_compare(picked.floatValue, [0.0, 1.0, 1.0, 1.0]))
        return ret

    def check_capture(self):
        draw = self.get_last_draw()

        self.check(draw is not None)

        draw = draw.previous

        self.controller.SetFrameEvent(draw.eventId, False)

        # Make an output so we can pick pixels
        self.out: rd.ReplayOutput = self.controller.CreateOutput(rd.CreateHeadlessWindowingData(100, 100), rd.ReplayOutputType.Texture)

        pipe: rd.PipeState = self.controller.GetPipelineState()

        self.tex = rd.TextureDisplay()
        self.tex.resourceId = pipe.GetOutputTargets()[0].resourceId
        self.out.SetTextureDisplay(self.tex)

        texdetails = self.get_texture(self.tex.resourceId)

        # Top left we expect a regular line segment.
        s = self.sample(0, 0)

        # All points should be the line color
        if not rdtest.value_compare(s, [True, True, True]):
            raise rdtest.TestFailureException("Normal line picked values {} doesn't match expectation".format(s))

        # Next row is unstippled. The lines should either be all present, or not present
        names = ["Rectangle", "Bresenham", "Rectangle Round"]
        for col in [0, 1, 2]:
            s = self.sample(1, col)

            n = "Unstippled {}".format(names[col])

            if s[0]:
                if not rdtest.value_compare(s, [True, True, True]):
                    raise rdtest.TestFailureException("{} picked values {} doesn't match expectation".format(n, s))
                rdtest.log.success("{} line looks as expected".format(n))
            else:
                if not rdtest.value_compare(s, [False, False, False]):
                    raise rdtest.TestFailureException("{} picked values {} doesn't match expectation".format(n, s))
                rdtest.log.success("{} line not supported".format(n))

        # Final row is stippled. The lines should be present on each end, and not present in the middle
        # (or not present at all)
        for col in [0, 1, 2]:
            s = self.sample(2, col)

            n = "Stippled {}".format(names[col])

            if s[0]:
                if not rdtest.value_compare(s, [True, False, True]):
                    raise rdtest.TestFailureException("{} picked values {} doesn't match expectation".format(n, s))
                rdtest.log.success("{} line looks as expected".format(n))
            else:
                if not rdtest.value_compare(s, [False, False, False]):
                    raise rdtest.TestFailureException("{} picked values {} doesn't match expectation".format(n, s))
                rdtest.log.success("{} line not supported".format(n))

        rdtest.log.success("All lines look as expected")

        self.out.Shutdown()
