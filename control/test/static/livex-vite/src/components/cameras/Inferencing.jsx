import React from 'react';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';
import { Container } from 'react-bootstrap';
import Form from 'react-bootstrap/Form';
import { useAdapterEndpoint, WithEndpoint, TitleCard } from 'odin-react';
import { FloatingLabel } from 'react-bootstrap';
import Button from 'react-bootstrap/Button';
import { useState } from 'react';

import { checkNull, checkNullNoDp, floatingInputStyle, floatingLabelStyle } from '../../utils';

const EndPointButton = WithEndpoint(Button);

function InferenceView(props) {
    const {endpoint_url} = props;
    const {name} = props;
 
    const inferenceEndPoint = useAdapterEndpoint('inference', endpoint_url, 1000);
    const inferenceResults = inferenceEndPoint?.data[name]?.results;

    const [flatfieldNum, setFlatfieldNum] = useState(0);
    const handleFlatfieldNumChange = (e) => {
      setFlatfieldNum(e.target.value);
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
                        value={checkNullNoDp(inferenceResults?.total_objects)}
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
                        value={checkNullNoDp(inferenceResults?.frame_number)}
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
                          value={inferenceResults?.ff_correction_file}
                          onChange={handleFlatfieldNumChange}
                        />
                    </FloatingLabel>
                  </Row>
                </Col>
                <Col>
                  <Row>
                    <EndPointButton
                      endpoint={inferenceEndPoint}
                      fullpath={`${name}/results/set_flatfield_num`}
                      value={flatfieldNum}>
                        Set flatfield from acquisition
                    </EndPointButton>
                  </Row>
                  <Row>
                    <EndPointButton
                      endpoint={inferenceEndPoint}
                      fullpath={`${name}/results/set_flatfield_num`}
                      value={-1 /*Special case adapter-side,*/} 
                      variant='danger'>
                        Clear flatfield
                    </EndPointButton>
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

