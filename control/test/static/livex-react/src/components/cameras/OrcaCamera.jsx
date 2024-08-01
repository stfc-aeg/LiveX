import React from 'react';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';
import { Container, Stack } from 'react-bootstrap';
import Form from 'react-bootstrap/Form';
import InputGroup from 'react-bootstrap/InputGroup';
import { useAdapterEndpoint, WithEndpoint, StatusBox, TitleCard, DropdownSelector, OdinDoubleSlider } from 'odin-react';
import Button from 'react-bootstrap/Button';
import { useState, useEffect } from 'react';
import { Dropdown } from 'react-bootstrap';

import { checkNullNoDp } from '../../utils';

import ClickableImage from './ClickableImage';

const EndPointFormControl = WithEndpoint(Form.Control);
const EndPointButton = WithEndpoint(Button);
const EndPointDropdownSelector = WithEndpoint(DropdownSelector);
const EndPointDoubleSlider = WithEndpoint(OdinDoubleSlider);
const EndPointSlider = WithEndpoint(Form.Range);

function OrcaCamera(props) {
    const {name} = props;
    const {connectedPuttingDisable} = props;

    const nameString = name.toString();
    let orcaAddress = 'camera/cameras/'+nameString;
    const orcaEndPoint = useAdapterEndpoint(orcaAddress, 'http://192.168.0.22:8888', 1000);

    let liveViewAddress = 'live_data/liveview/'+nameString;
    const liveViewEndPoint = useAdapterEndpoint(liveViewAddress, 'http://192.168.0.22:8888', 1000);
    const liveViewData = liveViewEndPoint?.data[name];


    // Array of camera status names
    const status = ['disconnected', 'connected', 'capturing'];
    // Current status of orcaCamera (for readability)
    const orcaStatus = orcaEndPoint?.data[name]?.status?.camera_status;

    // Colours
    const colourEffects = [
        'autumn', 'bone', 'jet', 'winter', 'rainbow', 'ocean', 'summer', 'spring',
        'cool', 'hsv', 'pink', 'hot', 'parula', 'magma', 'inferno', 'plasma',
        'viridis', 'cividis', 'twilight', 'twilight_shifted', 'turbo', 'deepgreen'
    ];

    const commonImageResolutions = [
        10, 25, 50, 75, 100
    ];

    // Handle image data
    const [width, setWidth] = useState('');
    const [height, setHeight] = useState('');
    const [dimensions, setDimensions] = useState('');

    const [roiX, setRoiX] = useState('');
    const [roiY, setRoiY] = useState('');
    const [roiBoundaries, setRoiBoundaries] = useState([[0, 100], [0, 100]]);

    const [histData, changeHistData] = useState([{}]);
    useEffect(() => {
        changeHistData(`data:image/jpg;base64,${liveViewData?.image?.histogram}`);
    }, [liveViewData?.image?.histogram]);

    const roiXChange = (e) => {
        let newRoiX = e.target.value;
        setRoiX(newRoiX);
        setRoiBoundaries([newRoiX, roiY]);
    }
    const roiYChange = (e) => {
        let newRoiY = e.target.value;
        setRoiY(newRoiY);
        setRoiBoundaries([roiX, newRoiY]);
    }

    const heightChange = (e) => {
        let newHeight = e.target.value;
        setHeight(newHeight);
        setDimensions([width, newHeight]);
    };
    const widthChange = (e) => {
        let newWidth = e.target.value;
        setWidth(newWidth);
        setDimensions([newWidth, height]);
    };

    return (
        <Container>
          <TitleCard title={orcaEndPoint?.data[name]?.camera_name + " control"}>
            <Col>
            <Row>
            <Col>
            <StatusBox as="span" label="Status">
                {(orcaStatus || "Not found" )}
            </StatusBox>
            <StatusBox label="Frame count">
                {checkNullNoDp(orcaEndPoint?.data[name]?.status.frame_number)}
            </StatusBox>
            </Col>
            {/* These buttons have variable output, display, and colour, depending on the camera status.
            Example, when the camera isn't connected, you can connect. If it's connected, you can disconnect.
            When capturing, that button is disabled - you need to move it out of that state first.*/}
            <Col>
            <EndPointButton // Move between statuses 1 and 0
                endpoint={orcaEndPoint}
                value={orcaStatus!==status[0] ? "disconnect" : "connect"}
                fullpath="command"
                event_type="click"
                disabled={![status[1], status[0]].includes(orcaStatus)}
                variant={orcaStatus!==status[0] ? "warning" : "success"}>
                {orcaStatus!==status[0] ? 'Disconnect' : 'Connect'}
            </EndPointButton>
            </Col>
            <Col>
            <EndPointButton // Move between statuses 3 and 1
                endpoint={orcaEndPoint}
                value={orcaStatus===status[2] ? "end_capture" : "capture"}
                fullpath="command"
                event_type="click"
                disabled={![status[2], status[1]].includes(orcaStatus)}
                variant={orcaStatus===status[2] ? "warning" : "success"}>
                {orcaStatus===status[2] ? 'Stop Capturing' : 'Capture'}
            </EndPointButton>
            </Col>
            </Row>
                <Stack>
                <InputGroup>
                    <InputGroup.Text>
                        command
                    </InputGroup.Text>
                    <EndPointFormControl
                        endpoint={orcaEndPoint}
                        type="text"
                        fullpath="command"
                        disabled={connectedPuttingDisable}>
                    </EndPointFormControl>
                </InputGroup>
                </Stack>

                <Stack>
                <InputGroup>
                    <InputGroup.Text>
                        exposure_time
                    </InputGroup.Text>
                    <EndPointFormControl
                        endpoint={orcaEndPoint}
                        type="number"
                        fullpath="config/exposure_time"
                        disabled={connectedPuttingDisable}>
                    </EndPointFormControl>
                </InputGroup>
                </Stack>

                <TitleCard title={`${orcaEndPoint?.data[name]?.camera_name} preview`}>
                    <Row>

                    <ClickableImage
                      endpoint={liveViewEndPoint}
                      imgSrc={liveViewData?.image?.data}
                      fullpath="image"
                      paramToUpdate="roi"
                      valuesAsPercentages={true}>
                    </ClickableImage>

                    <ClickableImage
                      endpoint={liveViewEndPoint}
                      imgSrc={liveViewData?.image?.histogram}
                      fullpath="image"
                      paramToUpdate="clip_range_percent"
                      maximiseAxis="y"
                      rectOutlineColour='black'
                      rectRgbaProperties='rgba(50,50,50,0.05)'
                      valuesAsPercentages={true}>
                    </ClickableImage>
                    </Row>
                    <Col>
                    <Form>
                    <InputGroup className="mt-3">
                    <InputGroup.Text>Image Colour Map</InputGroup.Text>
                        <EndPointDropdownSelector
                        endpoint={liveViewEndPoint}
                        event_type="select"
                        fullpath="image/colour"
                        buttonText={liveViewData?.image?.colour}
                        variant="outline-secondary">
                            {colourEffects.map((effect, index) => (
                                <Dropdown.Item
                                    key={index}
                                    eventKey={effect}>
                                        {effect}
                                </Dropdown.Item>
                            ))}
                        </EndPointDropdownSelector>
                      </InputGroup>

                    <Row>
                      <Col xs="6">
                        <InputGroup>
                            <InputGroup.Text>
                                Image Width
                            </InputGroup.Text>
                            <Form.Control
                            type="number"
                            placeholder={liveViewData?.image.size_x || "Width"}
                            value={width}
                            onChange={widthChange}
                            />
                        </InputGroup>

                        <InputGroup>
                            <InputGroup.Text>
                                Image Height
                            </InputGroup.Text>
                            <Form.Control
                            type="number"
                            placeholder={liveViewData?.image.size_y || "Height"}
                            value={height}
                            onChange={heightChange}
                            />
                        </InputGroup>
                      </Col>
                      <Col xs="6" className="mt-3">
                        <EndPointButton
                        endpoint={liveViewEndPoint}
                        value={dimensions}
                        fullpath={"image/dimensions"}
                        event_type="click"
                        variant="outline-primary"
                        className="mb-2">
                            Update image dimensions
                        </EndPointButton>
                      </Col>
                    </Row>
                    <Row className="mt-3">
                      <Col xs="8">
                        <Form>
                          <Form.Label>Resolution. Current: {liveViewData?.image?.resolution}</Form.Label>
                          <EndPointSlider
                          endpoint={liveViewEndPoint}
                          fullpath="image/resolution"
                          min={1}
                          max={100}
                          step={1}
                          ></EndPointSlider>
                        </Form>
                      </Col>
                      <Col xs="4">
                      <InputGroup className="mt-3">
                        <InputGroup.Text>Common Resolutions (%)</InputGroup.Text>
                        <EndPointDropdownSelector
                          endpoint={liveViewEndPoint}
                          event_type="select"
                          fullpath="image/resolution"
                          buttonText={liveViewData?.image?.resolution}
                          variant="outline-secondary">
                              {commonImageResolutions.map((effect, index) => (
                                <Dropdown.Item
                                    key={index}
                                    eventKey={effect}>
                                        {effect}
                                </Dropdown.Item>
                              ))}
                          </EndPointDropdownSelector>
                        </InputGroup>
                      </Col>
                    </Row>

                    <Row className="mt-3">
                    <EndPointDoubleSlider
                        endpoint={liveViewEndPoint}
                        fullpath="image/clip_range_value"
                        min="0"
                        max="65535"
                        steps="100"
                        title="Clipping range">
                    </EndPointDoubleSlider>
                    <EndPointButton
                        endpoint={liveViewEndPoint}
                        fullpath={"image/clip_range_value"}
                        event_type="click"
                        value={[0, 65535]}
                        variant="outline-primary">
                        Reset Clipping Range to 100%
                    </EndPointButton>
                    </Row>
                    <Row className="mt-3">
                        <EndPointButton
                          endpoint={liveViewEndPoint}
                          fullpath={"image/roi"}
                          event_type="click"
                          value={[[0, 100], [0, 100]]}
                          variant="outline-primary">
                            Reset Region of Interest to Full Image
                        </EndPointButton>
                    </Row>
                    </Form>
                    </Col>
                </TitleCard>
            </Col>
          </TitleCard>
        </Container>

    )
}

export default OrcaCamera;

