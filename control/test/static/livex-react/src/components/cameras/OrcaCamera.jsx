import React from 'react';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';
import { Container, Stack } from 'react-bootstrap';
import Form from 'react-bootstrap/Form';
import InputGroup from 'react-bootstrap/InputGroup';
import { useAdapterEndpoint, WithEndpoint, StatusBox, TitleCard, DropdownSelector } from 'odin-react';
import Button from 'react-bootstrap/Button';
import { useState, useEffect } from 'react';
import { Dropdown } from 'react-bootstrap';

const EndPointFormControl = WithEndpoint(Form.Control);
const EndPointButton = WithEndpoint(Button);
const EndPointDropdownSelector = WithEndpoint(DropdownSelector);

function OrcaCamera(props) {
    const {index} = props;
    const {connectedPuttingDisable} = props;

    const indexString = index.toString();
    let orcaAddress = 'camera/cameras/'+indexString;
    const orcaEndPoint = useAdapterEndpoint(orcaAddress, 'http://192.168.0.22:8888', 0);
    const orcaData = orcaEndPoint?.data[index];

    let liveViewAddress = 'live_data/liveview/'+indexString;
    const liveViewEndPoint = useAdapterEndpoint(liveViewAddress, 'http://192.168.0.22:8888', 1000);
    const liveViewData = liveViewEndPoint?.data[index];

    // Array of camera status names
    const status = ['disconnected', 'connected', 'capturing'];
    // Current status of orcaCamera (for readability)
    const orcaStatus = orcaData?.status?.camera_status;

    // Colours
    const colourEffects = [
        'autumn', 'bone', 'jet', 'winter', 'rainbow', 'ocean', 'summer', 'spring',
        'cool', 'hsv', 'pink', 'hot', 'parula', 'magma', 'inferno', 'plasma',
        'viridis', 'cividis', 'twilight', 'twilight_shifted', 'turbo', 'deepgreen'
    ];

    // Handle image data
    const [imgData, changeImgData] = useState([{}]);
    const [width, setWidth] = useState('');
    const [height, setHeight] = useState('');
    const [dimensions, setDimensions] = useState('');

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

    // Graph re-renders when data changes
    useEffect(() => {
        changeImgData(`data:image/jpg;base64,${liveViewData?.image?.data}`);
      }, [liveViewData?.image?.data]);

    return (

        <Container>
          <TitleCard title={orcaData?.camera_name + " control"}>
            <Col>
            <Row>
            <Col>
            <StatusBox as="span" label = "Status">
                {(orcaStatus || "Not found" )}
            </StatusBox>
            </Col>
            {/* These buttons have variable output, display, and colour, depending on the camera status.
            Example, you can connect the camera if it is off, and disconnect if it's connected.
            Otherwise, you can't interact with it. You'd need to disarm it first.*/}
            <Col>
            <EndPointButton // Move between statuses 1 and 0
                endpoint={orcaEndPoint}
                value={orcaStatus===status[1] ? "disconnect" : "connect"}
                fullpath="command"
                event_type="click"
                disabled={![status[1], status[0]].includes(orcaStatus)}
                variant={orcaStatus===status[1] ? "warning" : "success"}>
                {orcaStatus===status[1] ? 'Disconnect' : 'Connect'}
            </EndPointButton>
            </Col>
            <Col>
            <EndPointButton // Move between statuses 3 and 2
                endpoint={orcaEndPoint}
                value={orcaStatus===status[2] ? "discapture" : "capture"}
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

                <TitleCard title={`${orcaData?.camera_name} preview`}>
                    <Row>
                    {imgData && <img src={imgData} alt="Fetched"/>}
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
                      <Col>
                        
                      </Col>
                    </Row>
                    <InputGroup>
                        <InputGroup.Text>
                            Image Width
                        </InputGroup.Text>
                        <Form.Control
                        type="number"
                        placeholder="Width"
                        value={width}
                        onChange={widthChange}
                        />
                    </InputGroup>

                    <InputGroup>
                        <InputGroup.Text>
                            Image Width
                        </InputGroup.Text>
                        <Form.Control
                        type="number"
                        placeholder="Height"
                        value={height}
                        onChange={heightChange}
                        />
                    </InputGroup>

                    <EndPointButton
                    endpoint={liveViewEndPoint}
                    value={dimensions}
                    fullpath={"image/dimensions"}
                    event_type="click"
                    variant="outline-primary"
                    className="mb-3">
                        Update image dimensions
                    </EndPointButton>
                    </Form>
                    </Col>
                </TitleCard>

            </Col>
          </TitleCard>
        </Container>

    )
}

export default OrcaCamera;

