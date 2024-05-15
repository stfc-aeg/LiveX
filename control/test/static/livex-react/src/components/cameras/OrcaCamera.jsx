import React from 'react';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';
import { Container, Stack } from 'react-bootstrap';
import Form from 'react-bootstrap/Form';
import InputGroup from 'react-bootstrap/InputGroup';
import { useAdapterEndpoint, WithEndpoint, StatusBox, TitleCard } from 'odin-react';
import Button from 'react-bootstrap/Button';
import { useState, useEffect } from 'react';
import ColourMapAccordion from './ColourMapAccordion';

const EndPointFormControl = WithEndpoint(Form.Control);
const EndPointButton = WithEndpoint(Button);

function OrcaCamera(props) {
    const {index} = props;
    const {connectedPuttingDisable} = props;

    const indexString = index.toString();
    let orcaAddress = 'camera/cameras/'+indexString;
    const orcaEndPoint = useAdapterEndpoint(orcaAddress, 'http://192.168.0.22:8888', 0);
    const orcaData = orcaEndPoint?.data[index];

    let liveViewAddress = 'live_data/liveview/'+indexString;
    const liveViewEndPoint = useAdapterEndpoint(liveViewAddress, 'http://192.168.0.22:8888', 500);
    const liveViewData = liveViewEndPoint?.data[index];

    console.log(liveViewData);

    // Array of camera status names
    const status = ['disconnected', 'connected', 'armed', 'capturing'];
    // Current status of orcaCamera (for readability)
    const orcaStatus = orcaData?.status?.camera_status;

    const [imgData, changeImgData] = useState([{}]);
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
            <EndPointButton // Move between statuses 2 and 1
                endpoint={orcaEndPoint}
                value={orcaStatus===status[2] ? "disarm" : "arm"}
                fullpath="command"
                event_type="click"
                disabled={![status[2], status[1]].includes(orcaStatus)}
                variant={orcaStatus===status[2] ? "warning" : "success"}>
                {orcaStatus===status[2] ? 'Disarm' : 'Arm'}
            </EndPointButton>
            </Col>
            <Col>
            <EndPointButton // Move between statuses 3 and 2
                endpoint={orcaEndPoint}
                value={orcaStatus===status[3] ? "discapture" : "capture"}
                fullpath="command"
                event_type="click"
                disabled={![status[3], status[2]].includes(orcaStatus)}
                variant={orcaStatus===status[3] ? "warning" : "success"}>
                {orcaStatus===status[3] ? 'Stop Capturing' : 'Capture'}
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

                <TitleCard title={`${orcaData?.camera_name} preview settings`}>
                    <Col>
                    <InputGroup>
                        <InputGroup.Text xs={3}>
                        Image Width
                        </InputGroup.Text>
                        <EndPointFormControl
                            endpoint={liveViewEndPoint}
                            type="number"
                            fullpath={"image/size_x"}
                            disabled={connectedPuttingDisable}>
                        </EndPointFormControl>
                    </InputGroup>
                    <InputGroup>
                        <InputGroup.Text xs={3}>
                        Image Height
                        </InputGroup.Text>
                        <EndPointFormControl
                            endpoint={liveViewEndPoint}
                            type="number"
                            fullpath={"image/size_y"}
                            disabled={connectedPuttingDisable}>
                        </EndPointFormControl>
                    </InputGroup>
                    
                    <ColourMapAccordion
                    liveViewEndPoint={liveViewEndPoint}
                    index={index}/>
                    </Col>
                </TitleCard>
                {imgData && <img src={imgData} alt="Fetched"/>}

            </Col>
          </TitleCard>
        </Container>

    )
}

export default OrcaCamera;

