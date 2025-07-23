import React from 'react';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';
import { Container, Stack } from 'react-bootstrap';
import Form from 'react-bootstrap/Form';
import InputGroup from 'react-bootstrap/InputGroup';
import { useAdapterEndpoint, WithEndpoint, TitleCard, OdinDoubleSlider } from 'odin-react';
import DropdownSelector from '../DropdownSelector';
import Button from 'react-bootstrap/Button';
import { useState } from 'react';
import { Dropdown } from 'react-bootstrap';
import { FloatingLabel } from 'react-bootstrap';

import { checkNullNoDp, floatingInputStyle, floatingLabelStyle } from '../../utils';

import ClickableImage from './ClickableImage';

const EndPointFormControl = WithEndpoint(Form.Control);
const EndPointButton = WithEndpoint(Button);
const EndPointDropdownSelector = WithEndpoint(DropdownSelector);
const EndPointDoubleSlider = WithEndpoint(OdinDoubleSlider);
const EndPointSlider = WithEndpoint(Form.Range);
const EndPointSelect = WithEndpoint(Form.Select);

function OrcaCamera(props) {
    const {endpoint_url} = props;
    const {name} = props;
    const {connectedPuttingDisable} = props;

    const nameString = name.toString();
    let orcaAddress = 'camera/cameras/'+nameString;
    const orcaEndPoint = useAdapterEndpoint(orcaAddress, endpoint_url, 1000);
 
    const liveViewEndPoint = useAdapterEndpoint('live_data', endpoint_url, 1000);
    const liveViewData = liveViewEndPoint?.data[name];

    // let imgAddress = 'live_data/_image/'+nameString;
    // const imgEndPoint = useAdapterEndpoint(imgAddress, endpoint_url, 1000);
    // const imgData = imgEndPoint?.data;

    // Array of camera status names
    const status = ['disconnected', 'connected', 'capturing'];
    // Current status of orcaCamera (for readability)
    const orcaStatus = orcaEndPoint?.data[name]?.status?.camera_status;
    const orcaConnected = orcaEndPoint?.data[name]?.connection?.connected;

    // Colours
    const colourEffects = [
        'autumn', 'bone', 'jet', 'winter', 'rainbow', 'ocean', 'summer', 'spring',
        'cool', 'hsv', 'pink', 'hot', 'parula', 'magma', 'inferno', 'plasma',
        'viridis', 'cividis', 'twilight', 'twilight_shifted', 'turbo', 'deepgreen'
    ];

    const commonImageResolutions = [
        10, 25, 50, 75, 100
    ];

    const labelWidth = 80;

    // Handle image data
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

    /* The titlecard buttons have variable output, display, and colour, depending on the camera status.
    Example, when the camera isn't connected, you can connect. If it's connected, you can disconnect.
    When capturing, that button is disabled - you need to move it out of that state first.*/
    return (
        <Container>
          <TitleCard title={
            <Row>
              <Col xs={3} className="d-flex align-items-center" style={{fontSize:'1.3rem'}}>
                {orcaEndPoint?.data[name]?.camera_name + " control"}
              </Col>
              <Col>
                {orcaConnected ? (
                <Row>
                  <Col xs={3}>
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
                  <Col xs={3}>
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
                ) : (
                <Col>
                  <EndPointButton
                    endpoint={orcaEndPoint}
                    value={true}
                    fullpath="connection/reconnect"
                    event_type="click"
                    disabled={orcaConnected}
                    variant={orcaConnected ? "info" : "danger"}>
                    {orcaConnected ? 'Connected' : 'Reconnect'}
                  </EndPointButton>
                </Col>
                )}
              </Col>
            </Row>
          }>
            <Col>
              <Row className="mb-3">
                <Col xs={4}>
                  <FloatingLabel
                    label="Status">
                      <Form.Control
                        plaintext
                        readOnly
                        style={floatingLabelStyle}
                        value={(orcaStatus || "Not found")}
                      />
                  </FloatingLabel>
                </Col>
                <Col xs={4}>
                  <FloatingLabel
                    label="Frame Count">
                      <Form.Control
                        plaintext
                        readOnly
                        style={floatingLabelStyle}
                        value={checkNullNoDp(orcaEndPoint?.data[name]?.status.frame_number)}
                      />
                  </FloatingLabel>
                </Col>
                <Col xs={4}>
                  <FloatingLabel
                    label="Cam Temp. (C)">
                      <Form.Control
                        plaintext
                        readOnly
                        style={floatingLabelStyle}
                        value={checkNullNoDp(orcaEndPoint?.data[name]?.status?.camera_temperature || "Not found")}
                      />
                  </FloatingLabel>
                </Col>
              </Row>
              <Stack>
              <InputGroup>
                <InputGroup.Text>
                    exposure_time
                </InputGroup.Text>
                <EndPointFormControl
                    endpoint={orcaEndPoint}
                    type="number"
                    fullpath="config/exposure_time"
                    event_type="enter"
                    disabled={connectedPuttingDisable}>
                </EndPointFormControl>
              </InputGroup>
              </Stack>

              <TitleCard title={`${orcaEndPoint?.data[name]?.camera_name} preview`}>
                <Row>
                  <ClickableImage
                    id={`image-${name}`}
                    endpoint={liveViewEndPoint}
                    imgPath={`_image/${name}/image`}
                    coordsPath={`${name}/image`}
                    coordsParam="roi"
                    valuesAsPercentages={true}>
                  </ClickableImage>
                  </Row>
                  <Row>
                  <ClickableImage
                    id={`histogram-${name}`}
                    endpoint={liveViewEndPoint}
                    imgPath={`_image/${name}/histogram`}
                    coordsPath={`${name}/image`}
                    coordsParam="clip_range_percent"
                    maximiseAxis="y"
                    rectOutlineColour='black'
                    rectRgbaProperties='rgba(50,50,50,0.05)'
                    valuesAsPercentages={true}>
                  </ClickableImage>
                </Row>
                <Row className="mt-3">
                  <Col xs={12} sm={6} 
                    style={{
                      alignItems: 'center',
                      justifyContent: 'center',
                      display:'flex'
                    }}>
                    <EndPointButton
                      endpoint={liveViewEndPoint}
                      fullpath={`${name}/image/clip_range_value`}
                      event_type="click"
                      value={[0, 65535]}
                      variant="primary">
                      Reset Clipping Range to 100%
                    </EndPointButton>
                  </Col>
                  <Col xs={12} sm={6} 
                    style={{
                      alignItems: 'center',
                      justifyContent: 'center',
                      display:'flex'
                    }}>
                    <EndPointButton
                      endpoint={liveViewEndPoint}
                      fullpath={`${name}/image/roi`}
                      event_type="click"
                      value={[[0, 100], [0, 100]]}
                      variant="primary">
                        Reset Region of Interest to Full Image
                    </EndPointButton>
                  </Col>
                </Row>
                <Row className="mt-3">
                  <Col xs={6}>
                    <FloatingLabel
                      label="Image Colour Map">
                        <EndPointSelect
                          endpoint={liveViewEndPoint}
                          fullpath={`${name}/image/colour`}
                          buttonText={liveViewData?.image?.colour}
                          style={floatingInputStyle}>
                            {colourEffects.map(
                              (effect, index) => (
                                <option value={index} key={index}>
                                  {effect}
                                </option>
                            ))}
                          </EndPointSelect>
                    </FloatingLabel>
                  </Col>
                  <Col xs={6}>
                    <FloatingLabel
                      label="Resolution (%)">
                        <EndPointSelect
                          endpoint={liveViewEndPoint}
                          fullpath={`${name}/image/resolution`}
                          buttonText={liveViewData?.image?.resolution}
                          style={floatingInputStyle}>
                            {commonImageResolutions.map((effect, index) => (
                              <option value={index} key={index}>
                                {effect}
                              </option>
                              ))
                            }
                        </EndPointSelect>
                    </FloatingLabel>
                  </Col>
                </Row>
              </TitleCard>
            </Col>
          </TitleCard>
        </Container>
    )
}

export default OrcaCamera;

