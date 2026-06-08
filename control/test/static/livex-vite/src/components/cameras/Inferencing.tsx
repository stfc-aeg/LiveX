import type { AdapterEndpoint } from 'odin-react';
import type { InferenceEndpointTypes } from '../../EndpointTypes';

import { Row, Col, Container, Form, FloatingLabel, Button } from 'react-bootstrap';
import { useAdapterEndpoint, TitleCard, EndpointButton } from 'odin-react';
import { useState } from 'react';
import { checkNull, checkNullNoDp, floatingInputStyle, floatingLabelStyle } from '../../utils';

interface InferenceViewProps {
  endpoint_url: string;
  name: string;
}

function InferenceView(props: InferenceViewProps) {
    const {endpoint_url, name} = props;

 
    const inferenceEndPoint = useAdapterEndpoint<InferenceEndpointTypes>('inference', endpoint_url, 1000);
    const inferenceResults = inferenceEndPoint?.data?.[name]?.results;

    const [flatfieldNum, setFlatfieldNum] = useState(0);
    const handleFlatfieldNumChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      setFlatfieldNum(Number(e.target.value));
    };

    return (
        <Container>
          { inferenceResults && (
          <TitleCard title={`${name} Inference Details`}>
            <Col>
              <Row className="mb-3">
                <Col xs={4}>
                  <FloatingLabel
                    label="# Objects">
                      <Form.Control
                        plaintext
                        readOnly
                        style={floatingLabelStyle}
                        value={checkNullNoDp(inferenceResults?.num_predictions)}
                      />
                  </FloatingLabel>
                </Col>
                <Col xs={4}>
                  <FloatingLabel
                    label="Frame #">
                      <Form.Control
                        plaintext
                        readOnly
                        style={floatingLabelStyle}
                        value={checkNullNoDp(inferenceResults?.last_frame_number)}
                      />
                  </FloatingLabel>
                </Col>
                <Col xs={4}>
                  <FloatingLabel
                    label="Avg Inf. Time">
                      <Form.Control
                        plaintext
                        readOnly
                        style={floatingLabelStyle}
                        value={checkNull(inferenceResults?.avg_inference_time_ms)}
                      />
                  </FloatingLabel>
                </Col>
              </Row>
              <Row className='mt-3'>
                <Col xs={3}></Col>
                <Col>
                  <Row className="mt-2">
                    <FloatingLabel
                      label="Flatfield Acquisition #">
                        <Form.Control
                          style={floatingInputStyle}
                          type="number"
                          value={inferenceResults?.flatfield_file}
                          onChange={handleFlatfieldNumChange}
                        />
                    </FloatingLabel>
                  </Row>
                </Col>
                <Col>
                  <Row>
                    <EndpointButton
                      endpoint={inferenceEndPoint}
                      fullpath={`${name}/results/set_flatfield_num`}
                      value={flatfieldNum}>
                        Set flatfield from acquisition
                    </EndpointButton>
                  </Row>
                  <Row>
                    <EndpointButton
                      endpoint={inferenceEndPoint}
                      fullpath={`${name}/results/set_flatfield_num`}
                      value={-1 /*Special case adapter-side,*/} 
                      variant='danger'>
                        Clear flatfield
                    </EndpointButton>
                  </Row>
                </Col>
              </Row>
            </Col>
          </TitleCard>
          )}
        </Container>
    )
}

export default InferenceView;

