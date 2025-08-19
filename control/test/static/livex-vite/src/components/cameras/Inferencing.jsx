import React from 'react';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';
import { Container } from 'react-bootstrap';
import Form from 'react-bootstrap/Form';
import { useAdapterEndpoint, TitleCard } from 'odin-react';
import { FloatingLabel } from 'react-bootstrap';

import { checkNull, checkNullNoDp, floatingLabelStyle } from '../../utils';


function InferenceView(props) {
    const {endpoint_url} = props;
    const {name} = props;
 
    const inferenceEndPoint = useAdapterEndpoint('inference', endpoint_url, 1000);
    const inferenceResults = inferenceEndPoint?.data[name]?.results;

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
            </Col>
          </TitleCard>
          )}
        </Container>
    )
}

export default InferenceView;

