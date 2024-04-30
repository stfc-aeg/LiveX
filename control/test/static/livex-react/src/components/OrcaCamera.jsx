import React from 'react';
import Col from 'react-bootstrap/Col';
import { Container, Stack } from 'react-bootstrap';
import { useState, useEffect } from 'react';
import Form from 'react-bootstrap/Form';
import InputGroup from 'react-bootstrap/InputGroup';
import { WithEndpoint, OdinGraph } from 'odin-react';

let render = 0;

const EndPointFormControl = WithEndpoint(Form.Control);

function OrcaCamera(props) {
    const {index} = props;
    const {name} = props;
    const {cameraEndPoint} = props;
    const {liveViewEndPoint} = props;
    const {connectedPuttingDisable} = props;

    const [imgData, changeImgData] = useState([{}]);

    // Graph re-renders when data changes
    useEffect(() => {
        if (liveViewEndPoint.data?.data) {
          render++;
          const base64Data = liveViewEndPoint.data.data;
          const decodedData = atob(base64Data);

          const eightBit = new Uint8Array(decodedData.length);
          for (let i=0; i<decodedData.length; i++) {
            eightBit[i] = decodedData.charCodeAt(i);
          }

          const arrayData = new Uint16Array(eightBit.buffer);
          console.log(arrayData);
          changeImgData(arrayData);

        }
      }, [liveViewEndPoint.data?.data]);

      console.log("component render number: ", render);

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
                        fullpath={"cameras/" + index.toString() + "/command"}
                        disabled={connectedPuttingDisable}>
                    </EndPointFormControl>
                    <OdinGraph
                        title={name}
                        prop_data={imgData}
                        num_x={512}
                        type="heatmap"
                        colorscale="Greys">
                    </OdinGraph>
                </InputGroup>
                </Stack>
            </Col>
        </Container>

    )
}

export default OrcaCamera;

