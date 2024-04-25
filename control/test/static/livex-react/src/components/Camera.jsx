import React from 'react';
import Col from 'react-bootstrap/Col';
import { Container, Stack } from 'react-bootstrap';
import { useState, useEffect } from 'react';
import Form from 'react-bootstrap/Form';
import InputGroup from 'react-bootstrap/InputGroup';
import { TitleCard, WithEndpoint, ToggleSwitch, StatusBox, DropdownSelector, OdinGraph } from 'odin-react';



const EndPointFormControl = WithEndpoint(Form.Control);
const EndpointDropdown = WithEndpoint(DropdownSelector);

function Camera(props) {
    const {cameraEndPoint} = props;
    const {liveViewEndPoint} = props;
    const {connectedPuttingDisable} = props;

    const [imgData, changeImgData] = useState([{}]);

    // Graph re-renders when data changes
    useEffect(() => {
        if (liveViewEndPoint.data?.data) {
          const base64Data = liveViewEndPoint.data.data;
          const decodedData = atob(base64Data);
          console.log(decodedData);
          const arrayData = new Uint8Array(decodedData.split('').map(char => char.charCodeAt(0)));
          changeImgData(arrayData);
          console.log(arrayData);
        }
      }, [liveViewEndPoint.data?.data]);

    return (

        <Container>
            <Col>
                <Stack>
                <InputGroup>
                    <InputGroup.Text>
                        command
                    </InputGroup.Text>
                    <EndPointFormControl
                        endpoint={cameraEndPoint}
                        type="text"
                        fullpath={"command"}
                        disabled={connectedPuttingDisable}>
                    </EndPointFormControl>
                    <OdinGraph
                        title="preview"
                        prop_data={imgData}
                        num_x={4096}
                        num_y={2304}
                        type="heatmap">
                    </OdinGraph>
                </InputGroup>
                </Stack>
            </Col>
        </Container>

    )
}

export default Camera;

